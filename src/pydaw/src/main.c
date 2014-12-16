/*
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/


//Required for sched.h
#ifndef __USE_GNU
#define __USE_GNU
#endif

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <sndfile.h>
#include <pthread.h>
#include <limits.h>
#include <portaudio.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <math.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <signal.h>
#include <dirent.h>
#include <time.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <errno.h>

#include <lo/lo.h>

//  If you define this, you must also link to cpufreq appropriately with
//    LDFLAGS+="-lcpufreq"  //or whatever flag
//  #define PYDAW_CPUFREQ

#ifdef PYDAW_CPUFREQ
#include <cpufreq.h>
#endif

#include <linux/sched.h>

#include "compiler.h"
#include "pydaw_files.h"
#include "../include/pydaw_plugin.h"
#include "../libmodsynth/lib/lmalloc.h"
#include "mk_threads.h"
#include "midi_device.h"

#define CLOCKID CLOCK_REALTIME
#define SIG SIGRTMIN

#define PA_SAMPLE_TYPE paFloat32
#define DEFAULT_FRAMES_PER_BUFFER 512

static float **pluginOutputBuffers;


t_midi_device_list MIDI_DEVICES;
lo_server_thread serverThread;

static sigset_t _signals;

int PYDAW_NO_HARDWARE = 0;
PmError f_midi_err;

void osc_error(int num, const char *m, const char *path);

int osc_message_handler(const char *path, const char *types, lo_arg **argv, int
		      argc, void *data, void *user_data) ;
int osc_debug_handler(const char *path, const char *types, lo_arg **argv, int
		      argc, void *data, void *user_data) ;

inline void v_pydaw_run_main_loop(int sample_count,
        float **output, float **a_input_buffers);

void signalHandler(int sig)
{
    printf("signal %d caught, trying to clean up and exit\n", sig);
    exiting = 1;
}


#ifdef PYDAW_CPUFREQ

void v_pydaw_restore_cpu_governor()
{
    int f_cpu_count = sysconf( _SC_NPROCESSORS_ONLN );
    int f_i = 0;
    while(f_i < f_cpu_count)
    {
        struct cpufreq_policy * f_policy = cpufreq_get_policy(f_i);
        printf("Restoring CPU governor for CPU %i, was set to %s\n",
                f_i, f_policy->governor);
        sprintf(f_policy->governor, "ondemand");
        cpufreq_set_policy(f_i, f_policy);
        ++f_i;
    }
}

void v_pydaw_set_cpu_governor()
{
    printf("Attempting to set CPU governor to 'performance'\n");
    int f_cpu_count = sysconf( _SC_NPROCESSORS_ONLN );
    int f_i = 0;
    while(f_i < f_cpu_count)
    {
        struct cpufreq_policy * f_policy = cpufreq_get_policy(f_i);
        sprintf(f_policy->governor, "performance");
        cpufreq_set_policy(f_i, f_policy);
        ++f_i;
    }
}

#endif


static void midiTimerCallback(int sig, siginfo_t *si, void *uc)
{
    int f_i;
    t_midi_device * f_device;

    for(f_i = 0; f_i < MIDI_DEVICES.count; ++f_i)
    {
        f_device = &MIDI_DEVICES.devices[f_i];
        if(f_device->loaded)
        {
            midiPoll(f_device);
        }
    }
}

inline void v_pydaw_run(float ** buffers, int sample_count)
{
    pthread_spin_lock(&musikernel->main_lock);

    if(!musikernel->is_offline_rendering)
    {
        musikernel->input_buffers_active = 1;

        v_pydaw_run_main_loop(sample_count, buffers, NULL);
    }
    else
    {
        /*Clear the output buffer*/
        musikernel->input_buffers_active = 0;
        register int f_i = 0;

        while(f_i < sample_count)
        {
            buffers[0][f_i] = 0.0f;
            buffers[1][f_i] = 0.0f;
            ++f_i;
        }
    }

    pthread_spin_unlock(&musikernel->main_lock);
}

inline void v_pydaw_run_main_loop(int sample_count,
        float ** a_buffers, PYFX_Data **a_input_buffers)
{
    musikernel->current_host->run(sample_count, a_buffers, a_input_buffers);

    if(musikernel->is_previewing)
    {
        register int f_i = 0;
        t_pydaw_audio_item * f_audio_item = musikernel->preview_audio_item;
        t_wav_pool_item * f_wav_item = musikernel->preview_wav_item;
        while(f_i < sample_count)
        {
            if(f_audio_item->sample_read_heads[0].whole_number >=
                f_wav_item->length)
            {
                musikernel->is_previewing = 0;
                break;
            }
            else
            {
                v_adsr_run_db(&f_audio_item->adsrs[0]);
                if(f_wav_item->channels == 1)
                {
                    float f_tmp_sample = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[0]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)) *
                        (f_audio_item->adsrs[0].output) *
                        (musikernel->preview_amp_lin); // *
                        //(f_audio_item->fade_vol);

                    a_buffers[0][f_i] = f_tmp_sample;
                    a_buffers[1][f_i] = f_tmp_sample;
                }
                else if(f_wav_item->channels > 1)
                {
                    a_buffers[0][f_i] = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[0]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)) *
                        (f_audio_item->adsrs[0].output) *
                        (musikernel->preview_amp_lin); // *
                    //(f_audio_item->fade_vol);

                    a_buffers[1][f_i] = f_cubic_interpolate_ptr_ifh(
                        (f_wav_item->samples[1]),
                        (f_audio_item->sample_read_heads[0].whole_number),
                        (f_audio_item->sample_read_heads[0].fraction)) *
                        (f_audio_item->adsrs[0].output) *
                        (musikernel->preview_amp_lin); // *
                        //(f_audio_item->fade_vol);
                }

                v_ifh_run(&f_audio_item->sample_read_heads[0],
                        f_audio_item->ratio);

                if((f_audio_item->sample_read_heads[0].whole_number)
                    >= (musikernel->preview_max_sample_count))
                {
                    v_adsr_release(&f_audio_item->adsrs[0]);
                }

                if(f_audio_item->adsrs[0].stage == ADSR_STAGE_OFF)
                {
                    musikernel->is_previewing = 0;
                    break;
                }
            }
            ++f_i;
        }
    }

    if(!musikernel->is_offline_rendering && MASTER_VOL != 1.0f)
    {
        register int f_i;
        for(f_i = 0; f_i < sample_count; ++f_i)
        {
            a_buffers[0][f_i] *= MASTER_VOL;
            a_buffers[1][f_i] *= MASTER_VOL;
        }
    }
}

int THREAD_AFFINITY = 0;
int THREAD_AFFINITY_SET = 0;

static int portaudioCallback(
        const void *inputBuffer, void *outputBuffer,
        unsigned long framesPerBuffer,
        const PaStreamCallbackTimeInfo* timeInfo,
        PaStreamCallbackFlags statusFlags, void *userData)
{
    float *out = (float*)outputBuffer;

    if(unlikely(framesPerBuffer > FRAMES_PER_BUFFER))
    {
        printf("WARNING:  Audio device requested buffer size %i, "
            "truncating to max buffer size:  %i\n",
            (int)framesPerBuffer, FRAMES_PER_BUFFER);
        framesPerBuffer = FRAMES_PER_BUFFER;
    }

    (void)inputBuffer; //Prevent unused variable warning.

    // Try one time to set thread affinity
    if(unlikely(THREAD_AFFINITY && !THREAD_AFFINITY_SET))
    {
        v_self_set_thread_affinity();
        THREAD_AFFINITY_SET = 1;
    }

    v_pydaw_run(pluginOutputBuffers, framesPerBuffer);

    register int f_i;

    for(f_i = 0; f_i < framesPerBuffer; ++f_i)
    {
        *out++ = pluginOutputBuffers[0][f_i];  // left
        *out++ = pluginOutputBuffers[1][f_i];  // right
    }

    return paContinue;
}

typedef struct
{
    int pid;
}ui_thread_args;

__attribute__((optimize("-O0"))) void * ui_process_monitor_thread(
    void * a_thread_args)
{
    char f_proc_path[256];
    f_proc_path[0] = '\0';
    ui_thread_args * f_thread_args = (ui_thread_args*)(a_thread_args);
    sprintf(f_proc_path, "/proc/%i", f_thread_args->pid);
    struct stat sts;
    int f_exited = 0;

    while(!exiting)
    {
        sleep(1);
        if (stat(f_proc_path, &sts) == -1 && errno == ENOENT)
        {
            printf("UI process doesn't exist, exiting.\n");
            exiting = 1;
            f_exited = 1;
            break;
        }
    }

    if(f_exited)
    {
        sleep(3);
        exit(0);
    }

    return (void*)0;
}

#ifndef RTLD_LOCAL
#define RTLD_LOCAL  (0)
#endif

/* argv positional args:
 * [1] Install prefix (ie: /usr)
 * [2] Project path
 * [3] UI PID  //for monitoring that the UI hasn't crashed
 * Optional args:
 * --sleep
 */
__attribute__((optimize("-O0"))) int main(int argc, char **argv)
{
    if(argc < 5)
    {
        printf("\nUsage: %s install_prefix project_path ui_pid "
            "huge_pages[--sleep]\n\n", argv[0]);
        exit(9996);
    }

    float sample_rate = 44100.0f;
    int f_thread_count = 0;
    int f_thread_affinity = 0;
    int f_performance = 0;
    int j;

    //Stop trying to load the soundcard after 3 failed attempts
    int f_failure_count = 0;

    pthread_attr_t f_ui_threadAttr;
    struct sched_param param;
    param.__sched_priority = 1; //90;
    pthread_attr_init(&f_ui_threadAttr);
    pthread_attr_setschedparam(&f_ui_threadAttr, &param);
    pthread_attr_setstacksize(&f_ui_threadAttr, 1000000); //8388608);
    pthread_attr_setdetachstate(&f_ui_threadAttr, PTHREAD_CREATE_DETACHED);

    pthread_t f_ui_monitor_thread;
    ui_thread_args * f_ui_thread_args =
            (ui_thread_args*)malloc(sizeof(ui_thread_args));
    f_ui_thread_args->pid = atoi(argv[3]);
    pthread_create(&f_ui_monitor_thread, &f_ui_threadAttr,
            ui_process_monitor_thread, (void*)f_ui_thread_args);

    int f_huge_pages = atoi(argv[4]);
    assert(f_huge_pages == 0 || f_huge_pages == 1);

    if(f_huge_pages)
    {
        printf("Attempting to use hugepages\n");
    }

    USE_HUGEPAGES = f_huge_pages;

    j = 0;

    while(j < argc)
    {
        printf("%s\n", argv[j]);
        ++j;
    }

    if(setpriority(PRIO_PROCESS, 0, -20))
    {
        printf("Unable to renice process (this was to be expected if "
            "the process is not running as root)\n");
    }

    timer_t timerid;
    struct sigevent sev;
    struct itimerspec its;
    long long freq_nanosecs;
    sigset_t mask;
    struct sigaction sa;

    int f_usleep = 0;

    if(argc > 5)
    {
        j = 5;
        while(j < argc)
        {
            if(!strcmp(argv[j], "--sleep"))
            {
                f_usleep = 1;
            }
            else
            {
                printf("Invalid argument [%i] %s\n", j, argv[j]);
            }
            ++j;
        }
    }

    int f_current_proc_sched = sched_getscheduler(0);

    if(f_current_proc_sched == RT_SCHED)
    {
        printf("Process scheduler already set to real-time.");
    }
    else
    {
        printf("\n\nProcess scheduler set to %i, attempting to set "
                "real-time scheduler.", f_current_proc_sched);
        //Attempt to set the process priority to real-time
        const struct sched_param f_proc_param =
                {sched_get_priority_max(RT_SCHED)};
        printf("Attempting to set scheduler for process\n");
        sched_setscheduler(0, RT_SCHED, &f_proc_param);
        printf("Process scheduler is now %i\n\n", sched_getscheduler(0));
    }

    setsid();
    sigemptyset (&_signals);
    sigaddset(&_signals, SIGHUP);
    sigaddset(&_signals, SIGINT);
    sigaddset(&_signals, SIGQUIT);
    sigaddset(&_signals, SIGPIPE);
    sigaddset(&_signals, SIGTERM);
    sigaddset(&_signals, SIGUSR1);
    sigaddset(&_signals, SIGUSR2);
    pthread_sigmask(SIG_BLOCK, &_signals, 0);

    j = 0;

    hpalloc((void**)&pluginOutputBuffers, 2 * sizeof(float*));

    int f_i = 0;
    while(f_i < 2)
    {
        hpalloc(
            (void**)&pluginOutputBuffers[f_i],
            sizeof(float) * FRAMES_PER_BUFFER);
        ++f_i;
    }

    /*Initialize Portaudio*/
    PaStreamParameters inputParameters, outputParameters;
    PaStream *stream;
    PaError err;
    err = Pa_Initialize();
    //if( err != paNoError ) goto error;
    /* default input device */

    /*Initialize Portmidi*/
    f_midi_err = Pm_Initialize();
    int f_with_midi = 0;

    char f_midi_device_name[1024];
    sprintf(f_midi_device_name, "None");

    char f_device_file_path[2048];
    char * f_home = getenv("HOME");

    printf("using home folder: %s\n", f_home);

    sprintf(f_device_file_path, "%s/%s/config/device.txt",
        f_home, PYDAW_VERSION);

    char f_show_dialog_cmd[1024];

    sprintf(f_show_dialog_cmd,
        "python3 \"%s/lib/%s/pydaw/python/libpydaw/pydaw_device_dialog.py\"",
            argv[1], PYDAW_VERSION);

    char f_cmd_buffer[10000];
    f_cmd_buffer[0] = '\0';
    char f_device_name[1024];
    f_device_name[0] = '\0';

    int f_frame_count = DEFAULT_FRAMES_PER_BUFFER;
    int f_audio_input_count = 0;

    MIDI_DEVICES.count = 0;

    /* Create OSC thread */

    serverThread = lo_server_thread_new("19271", osc_error);
    lo_server_thread_add_method(serverThread, NULL, NULL, osc_message_handler,
            NULL);
    lo_server_thread_start(serverThread);

    char * f_key_char = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
    char * f_value_char = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);

    while(1)
    {
        if(f_failure_count > 4)
        {
            printf("Failed to load device 3 times, quitting...\n");
            exit(9996);
        }

        if(i_pydaw_file_exists(f_device_file_path))
        {
            printf("device.txt exists\n");
            t_2d_char_array * f_current_string = g_get_2d_array_from_file(
                    f_device_file_path, PYDAW_LARGE_STRING);
            f_device_name[0] = '\0';

            while(1)
            {
                v_iterate_2d_char_array(f_current_string);
                if(f_current_string->eof)
                {
                    break;
                }
                if(!strcmp(f_current_string->current_str, "") ||
                    f_current_string->eol)
                {
                    continue;
                }

                strcpy(f_key_char, f_current_string->current_str);
                v_iterate_2d_char_array_to_next_line(f_current_string);
                strcpy(f_value_char, f_current_string->current_str);

                if(!strcmp(f_key_char, "name"))
                {
                    sprintf(f_device_name, "%s", f_value_char);
                    printf("device name: %s\n", f_device_name);
                }
                else if(!strcmp(f_key_char, "bufferSize"))
                {
                    f_frame_count = atoi(f_value_char);
                    printf("bufferSize: %i\n", f_frame_count);
                }
                else if(!strcmp(f_key_char, "audioEngine"))
                {
                    int f_engine = atoi(f_value_char);
                    printf("audioEngine: %i\n", f_engine);
                    if(f_engine == 4 || f_engine == 5 || f_engine == 7)
                    {
                        PYDAW_NO_HARDWARE = 1;
                    }
                    else
                    {
                        PYDAW_NO_HARDWARE = 0;
                    }
                }
                else if(!strcmp(f_key_char, "sampleRate"))
                {
                    sample_rate = atof(f_value_char);
                    printf("sampleRate: %i\n", (int)sample_rate);
                }
                else if(!strcmp(f_key_char, "threads"))
                {
                    f_thread_count = atoi(f_value_char);
                    if(f_thread_count > 8)
                    {
                        f_thread_count = 8;
                    }
                    else if(f_thread_count < 0)
                    {
                        f_thread_count = 0;
                    }
                    printf("threads: %i\n", f_thread_count);
                }
                else if(!strcmp(f_key_char, "threadAffinity"))
                {
                    f_thread_affinity = atoi(f_value_char);
                    THREAD_AFFINITY = f_thread_affinity;
                    printf("threadAffinity: %i\n", f_thread_affinity);
                }
                else if(!strcmp(f_key_char, "performance"))
                {
                    f_performance = atoi(f_value_char);

                    printf("performance: %i\n", f_performance);
                }
                else if(!strcmp(f_key_char, "midiInDevice"))
                {
                    sprintf(f_midi_device_name, "%s", f_value_char);
                    printf("midiInDevice: %s\n", f_value_char);
                    int f_device_result = midiDeviceInit(
                        &MIDI_DEVICES.devices[MIDI_DEVICES.count],
                        f_midi_device_name);

                    if(f_device_result == 0)
                    {
                        printf("Succeeded\n");
                    }
                    else if(f_device_result == 1)
                    {
                        printf("Error, did not find MIDI device\n");
                        /*++f_failure_count;
                        sprintf(f_cmd_buffer, "%s \"%s %s\"", f_show_dialog_cmd,
                            "Error: did not find MIDI device:",
                            f_midi_device_name);
                        system(f_cmd_buffer);
                        continue;*/
                    }
                    else if(f_device_result == 2)
                    {
                        printf("Error, opening MIDI device\n");
                        /*++f_failure_count;
                        sprintf(f_cmd_buffer, "%s \"%s %s, %s\"",
                            f_show_dialog_cmd, "Error opening MIDI device: ",
                            f_midi_device_name, Pm_GetErrorText(f_midi_err));
                        system(f_cmd_buffer);
                        continue;*/
                    }

                    ++MIDI_DEVICES.count;
                    f_with_midi = 1;
                }
                else if(!strcmp(f_key_char, "audioInputs"))
                {
                    f_audio_input_count = atoi(f_value_char);
                    printf("audioInputs: %s\n", f_value_char);
                    assert(f_audio_input_count >= 0 &&
                        f_audio_input_count <= 128);
                }
                else
                {
                    printf("Unknown key|value pair: %s|%s\n",
                        f_key_char, f_value_char);
                }
            }

            g_free_2d_char_array(f_current_string);

        }
        else
        {
            ++f_failure_count;
            printf("%s does not exist, running %s\n",
                f_device_file_path, f_show_dialog_cmd);
            f_device_name[0] = '\0';
            system(f_show_dialog_cmd);

            if(i_pydaw_file_exists(f_device_file_path))
            {
                continue;
            }
            else
            {
                printf("It appears that the user closed the audio device "
                        "dialog without choosing a device, exiting.");
                exit(9998);
            }

        }

        if (inputParameters.device == paNoDevice)
        {
            sprintf(f_cmd_buffer, "%s \"%s\"", f_show_dialog_cmd,
                "Error: No default input device.");
            system(f_cmd_buffer);
            continue;
        }

        inputParameters.channelCount = f_audio_input_count;
        inputParameters.sampleFormat = PA_SAMPLE_TYPE;
        inputParameters.hostApiSpecificStreamInfo = NULL;

        if (outputParameters.device == paNoDevice)
        {
          sprintf(f_cmd_buffer, "%s \"%s\"",
                f_show_dialog_cmd, "Error: No default output device.");
          system(f_cmd_buffer);
          continue;
        }

        outputParameters.channelCount = 2; /* stereo output */
        outputParameters.sampleFormat = PA_SAMPLE_TYPE;
        outputParameters.hostApiSpecificStreamInfo = NULL;

        f_i = 0;
        int f_found_index = 0;
        while(f_i < Pa_GetDeviceCount())
        {
            const PaDeviceInfo * f_padevice = Pa_GetDeviceInfo(f_i);
            if(!strcmp(f_padevice->name, f_device_name))
            {
                outputParameters.device = f_i;
                inputParameters.device = f_i;
                f_found_index = 1;
                break;
            }
            ++f_i;
        }

        if(!f_found_index)
        {
            sprintf(f_cmd_buffer,
                "%s \"Did not find device '%s' on this system.\"",
                f_show_dialog_cmd, f_device_name);
            system(f_cmd_buffer);
            ++f_failure_count;
            continue;
        }

        PaDeviceInfo * f_device_info = Pa_GetDeviceInfo(inputParameters.device);

        inputParameters.suggestedLatency =
            f_device_info->defaultLowInputLatency;
        outputParameters.suggestedLatency =
            f_device_info->defaultLowOutputLatency;

        err = Pa_OpenStream(
            &stream, &inputParameters,
            &outputParameters, sample_rate, //SAMPLE_RATE,
            f_frame_count, //FRAMES_PER_BUFFER,
            /* we won't output out of range samples so don't bother
             * clipping them */
            0, /* paClipOff, */
            portaudioCallback, NULL);

        if(err != paNoError)
        {
            ++f_failure_count;
            sprintf(f_cmd_buffer, "%s \"%s %s\"", f_show_dialog_cmd,
                    "Error while opening audio device: ", Pa_GetErrorText(err));
            system(f_cmd_buffer);
            continue;
        }
        break;
    }

    free(f_key_char);
    free(f_value_char);

    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    signal(SIGHUP, signalHandler);
    signal(SIGQUIT, signalHandler);
    pthread_sigmask(SIG_UNBLOCK, &_signals, 0);

    v_pydaw_activate(f_thread_count, f_thread_affinity, argv[2],
        sample_rate, &MIDI_DEVICES);

    v_queue_osc_message("ready", "");

    // only for no-hardware mode
    float * f_portaudio_input_buffer;
    float * f_portaudio_output_buffer;

    if(!PYDAW_NO_HARDWARE)
    {
        err = Pa_StartStream(stream);
        if(err != paNoError)
        {
            sprintf(f_cmd_buffer, "%s \"%s\"", f_show_dialog_cmd,
                "Error: Unknown error while starting device.  Please "
                "re-configure your device and try starting MusiKernel again.");
            system(f_cmd_buffer);
            exiting = 1;
        }
        const PaStreamInfo * f_stream_info = Pa_GetStreamInfo(stream);
        printf("Actual output latency:\n\tseconds:  %f\n\tsamples:  %i\n",
            (float)f_stream_info->outputLatency,
            (int)(f_stream_info->outputLatency * f_stream_info->sampleRate));
        if((int)f_stream_info->sampleRate != (int)sample_rate)
        {
            printf("Warning:  Samplerate reported by the device does not "
                "match the selected sample rate.\n");
        }
    }
    else
    {
        f_portaudio_input_buffer =
            (float*)malloc(sizeof(float) * FRAMES_PER_BUFFER);
        f_portaudio_output_buffer =
            (float*)malloc(sizeof(float) * FRAMES_PER_BUFFER);
    }

    if(f_with_midi)
    {
        /* Establish handler for timer signal */

       sa.sa_flags = SA_SIGINFO;
       sa.sa_sigaction = midiTimerCallback;
       sigemptyset(&sa.sa_mask);
       if (sigaction(SIG, &sa, NULL) == -1)
       {
           //errExit("sigaction");
       }

       /* Block timer signal temporarily */

       sigemptyset(&mask);
       sigaddset(&mask, SIG);
       if (sigprocmask(SIG_SETMASK, &mask, NULL) == -1)
       {
           //errExit("sigprocmask");
       }

       /* Create the timer */

       sev.sigev_notify = SIGEV_SIGNAL;
       sev.sigev_signo = SIG;
       sev.sigev_value.sival_ptr = &timerid;
       if (timer_create(CLOCKID, &sev, &timerid) == -1)
       {
           //errExit("timer_create");
       }

       /* Start the timer */

       freq_nanosecs = 5000000;
       its.it_value.tv_sec = 0;  //freq_nanosecs / 1000000000;
       its.it_value.tv_nsec = freq_nanosecs;  // % 1000000000;
       its.it_interval.tv_sec = its.it_value.tv_sec;
       its.it_interval.tv_nsec = its.it_value.tv_nsec;

       if (timer_settime(timerid, 0, &its, NULL) == -1)
       {
           //errExit("timer_settime");
       }

    } //if(f_with_midi)


    while(!exiting)
    {
        if(PYDAW_NO_HARDWARE)
        {
            portaudioCallback(f_portaudio_input_buffer,
                    f_portaudio_output_buffer, 128, NULL,
                    (PaStreamCallbackFlags)NULL, NULL);

            if(f_usleep)
            {
                usleep(1000);
            }
        }
        else
        {
            sleep(1);
        }

    }

    if(f_with_midi)
    {
        timer_delete(timerid);
    }

    f_i = 0;
    while(f_i < MIDI_DEVICES.count)
    {
        if(MIDI_DEVICES.devices[f_i].loaded)
        {
            midiDeviceClose(&MIDI_DEVICES.devices[f_i]);
        }
        ++f_i;
    }

    if(!PYDAW_NO_HARDWARE)
    {
        err = Pa_CloseStream(stream);
        Pa_Terminate();
        Pm_Terminate();
    }

    v_pydaw_destructor();


#ifdef PYDAW_CPUFREQ
    if(f_performance)
    {
        v_pydaw_restore_cpu_governor();
    }
#endif

    sigemptyset (&_signals);
    sigaddset(&_signals, SIGHUP);
    pthread_sigmask(SIG_BLOCK, &_signals, 0);
    kill(0, SIGHUP);

    printf("MusiKernel main() returning\n\n\n");
    return 0;
}

void osc_error(int num, const char *msg, const char *path)
{
    printf("liblo server error %d in path %s: %s\n", num, path, msg);
}


int osc_debug_handler(const char *path, const char *types, lo_arg **argv,
                      int argc, void *data, void *user_data)
{
    int f_i = 0;

    printf("got unhandled OSC message:\npath: <%s>\n", path);
    while(f_i < argc)
    {
        printf("arg %d '%c' ", f_i, types[f_i]);
        lo_arg_pp((lo_type)types[f_i], argv[f_i]);
        printf("\n");
        ++f_i;
    }

    return 1;
}

int osc_message_handler(const char *path, const char *types, lo_arg **argv,
                        int argc, void *data, void *user_data)
{
    const char *key = (const char *)&argv[0]->s;
    const char *value = (const char *)&argv[1]->s;

    assert(!strcmp(types, "ss"));

    if(!strcmp(path, "/musikernel/edmnext"))
    {
        v_en_configure(key, value);
        return 0;
    }
    if(!strcmp(path, "/musikernel/wavenext"))
    {
        v_wn_configure(key, value);
        return 0;
    }
    else if(!strcmp(path, "/musikernel/master"))
    {
        v_mk_configure(key, value);
        return 0;
    }
    else
    {
        return osc_debug_handler(path, types, argv, argc, data, user_data);
    }
}

