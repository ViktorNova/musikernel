/* -*- c-basic-offset: 4 -*-  vi:set ts=8 sts=4 sw=4: */
/*
This file is part of the PyDAW project, Copyright PyDAW Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#define _BSD_SOURCE    1
#define _SVID_SOURCE   1
#define _ISOC99_SOURCE 1

//Required for sched.h
#ifndef __USE_GNU
#define __USE_GNU
#endif

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include "pydaw_files.h"
#include "../include/pydaw_plugin.h"
#include <portaudio.h>

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <dlfcn.h>
#include <unistd.h>
#include <math.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <signal.h>
#include <dirent.h>
#include <time.h>
#include <libgen.h>

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <errno.h>

#include <lo/lo.h>

#include "../libmodsynth/lib/lmalloc.h"
//  If you define this, you must also link to cpufreq appropriately with
//    LDFLAGS+="-lcpufreq"  //or whatever flag
//  #define PYDAW_CPUFREQ

#ifdef PYDAW_CPUFREQ
#include <cpufreq.h>
#endif

#include <linux/sched.h>

#include "main.h"
#include "synth.c"
#include "midi_device.h"

#define PYDAW_CONFIGURE_KEY_SS "ss"
#define PYDAW_CONFIGURE_KEY_OS "os"
#define PYDAW_CONFIGURE_KEY_SI "si"
#define PYDAW_CONFIGURE_KEY_SR "sr"
#define PYDAW_CONFIGURE_KEY_SAVE_ATM "sa"
#define PYDAW_CONFIGURE_KEY_PLAY "play"
#define PYDAW_CONFIGURE_KEY_REC "rec"
#define PYDAW_CONFIGURE_KEY_STOP "stop"
#define PYDAW_CONFIGURE_KEY_LOOP "loop"
#define PYDAW_CONFIGURE_KEY_TEMPO "tempo"
#define PYDAW_CONFIGURE_KEY_SOLO "solo"
#define PYDAW_CONFIGURE_KEY_MUTE "mute"
#define PYDAW_CONFIGURE_KEY_CHANGE_INSTRUMENT "ci"
#define PYDAW_CONFIGURE_KEY_SHOW_PLUGIN_UI "su"
#define PYDAW_CONFIGURE_KEY_SHOW_FX_UI "fx"

#define PYDAW_CONFIGURE_KEY_PREVIEW_SAMPLE "preview"
#define PYDAW_CONFIGURE_KEY_STOP_PREVIEW "spr"

#define PYDAW_CONFIGURE_KEY_AUDIO_ITEM_LOAD_ALL "ai"
#define PYDAW_CONFIGURE_KEY_ADD_TO_WAV_POOL "wp"

#define PYDAW_CONFIGURE_KEY_UPDATE_AUDIO_INPUTS "ua"
#define PYDAW_CONFIGURE_KEY_SET_OVERDUB_MODE "od"

#define PYDAW_CONFIGURE_KEY_LOAD_AB_OPEN "abo"
#define PYDAW_CONFIGURE_KEY_LOAD_AB_SET "abs"
#define PYDAW_CONFIGURE_KEY_WE_SET "we"
#define PYDAW_CONFIGURE_KEY_WE_EXPORT "wex"
#define PYDAW_CONFIGURE_KEY_PANIC "panic"
#define PYDAW_CONFIGURE_KEY_PITCH_ENV "penv"
#define PYDAW_CONFIGURE_KEY_RATE_ENV "renv"
//Update a single control for a per-audio-item-fx
#define PYDAW_CONFIGURE_KEY_PER_AUDIO_ITEM_FX "paif"
//Reload entire region for per-audio-item-fx
#define PYDAW_CONFIGURE_KEY_PER_AUDIO_ITEM_FX_REGION "par"
#define PYDAW_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL "pc"
#define PYDAW_CONFIGURE_KEY_CONFIGURE_PLUGIN "co"
#define PYDAW_CONFIGURE_KEY_GLUE_AUDIO_ITEMS "ga"
#define PYDAW_CONFIGURE_KEY_EXIT "exit"

#define PYDAW_CONFIGURE_KEY_MIDI_LEARN "ml"
#define PYDAW_CONFIGURE_KEY_LOAD_CC_MAP "cm"
#define PYDAW_CONFIGURE_KEY_MIDI_DEVICE "md"

#define PYDAW_CONFIGURE_KEY_WAVPOOL_ITEM_RELOAD "wr"
#define PYDAW_CONFIGURE_KEY_MASTER_VOL "mvol"
#define PYDAW_CONFIGURE_KEY_KILL_ENGINE "abort"
#define PYDAW_CONFIGURE_KEY_SET_POS "pos"

#define PYDAW_CONFIGURE_KEY_PLUGIN_INDEX "pi"
#define PYDAW_CONFIGURE_KEY_UPDATE_SEND "ts"
#define PYDAW_CONFIGURE_KEY_SEND_VOL "sv"

#define CLOCKID CLOCK_REALTIME
#define SIG SIGRTMIN

void v_pydaw_parse_configure_message(t_pydaw_data*, const char*, const char*);

#define PA_SAMPLE_TYPE paFloat32
#define DEFAULT_FRAMES_PER_BUFFER 512

static float sample_rate;

static d3h_instance_t *this_instance;

static PYFX_Handle    instanceHandles;

static int insTotal, outsTotal;
static float **pluginInputBuffers, **pluginOutputBuffers;

static int controlInsTotal, controlOutsTotal;
t_midi_device MIDI_DEVICE  __attribute__((aligned(16)));
//static char * osc_path_tmp = "osc.udp://localhost:19271/dssi/pydaw";
lo_server_thread serverThread;

static sigset_t _signals;

int exiting = 0;

int PYDAW_NO_HARDWARE = 0;
PmError f_midi_err;

void osc_error(int num, const char *m, const char *path);

int osc_message_handler(const char *path, const char *types, lo_arg **argv, int
		      argc, void *data, void *user_data) ;
int osc_debug_handler(const char *path, const char *types, lo_arg **argv, int
		      argc, void *data, void *user_data) ;

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
        f_i++;
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
        f_i++;
    }
}

#endif


static void midiTimerCallback(int sig, siginfo_t *si, void *uc)
{
    assert(0);
}

int THREAD_AFFINITY = 0;
int THREAD_AFFINITY_SET = 0;

static int portaudioCallback( const void *inputBuffer,
                              void *outputBuffer,
                              unsigned long framesPerBuffer,
                              const PaStreamCallbackTimeInfo* timeInfo,
                              PaStreamCallbackFlags statusFlags,
                              void *userData )
{
    unsigned int i;
    //int inCount;
    int outCount;

    float *out = (float*)outputBuffer;

    if(framesPerBuffer > FRAMES_PER_BUFFER)
    {
        printf("WARNING:  Audio device requested buffer size %i, "
            "truncating to max buffer size:  %i\n",
            (int)framesPerBuffer, FRAMES_PER_BUFFER);
        framesPerBuffer = FRAMES_PER_BUFFER;
    }

    (void) inputBuffer; //Prevent unused variable warning.

    // Try one time to set thread affinity
    if(THREAD_AFFINITY && !THREAD_AFFINITY_SET)
    {
        v_self_set_thread_affinity();
        THREAD_AFFINITY_SET = 1;
    }

    i = 0;
    outCount = 0;
    outCount += this_instance->plugin->outs;

    v_pydaw_run(instanceHandles, framesPerBuffer);

    for( i=0; i < framesPerBuffer; i++ )
    {
        *out++ = pluginOutputBuffers[0][i];  // left
        *out++ = pluginOutputBuffers[1][i];  // right
    }

    return paContinue;
}

typedef struct
{
    int pid;
}ui_thread_args;

void * ui_process_monitor_thread(void * a_thread_args)
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
int main(int argc, char **argv)
{
    if(argc < 4)
    {
        printf("\nUsage: %s install_prefix project_path ui_pid [--sleep]\n\n",
                argv[0]);
        exit(9996);
    }

    v_pydaw_constructor();

    d3h_dll_t *dll;
    d3h_plugin_t *plugin;

    int f_thread_count = 0;
    int f_thread_affinity = 0;
    int f_performance = 0;
    int j;
    int in, out, controlIn, controlOut;

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

    j = 0;

    while(j < argc)
    {
        printf("%s\n", argv[j]);
        j++;
    }


    timer_t timerid;
    struct sigevent sev;
    struct itimerspec its;
    long long freq_nanosecs;
    sigset_t mask;
    struct sigaction sa;

    int f_usleep = 0;

    if(argc >= 5)
    {
        j = 4;
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
            j++;
        }
    }

    int f_current_proc_sched = sched_getscheduler(0);

#ifdef SCHED_DEADLINE
    printf("Using SCHED_DEADLINE\n");
#else
    printf("Using SCHED_FIFO\n");
#endif

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

    insTotal = outsTotal = controlInsTotal = controlOutsTotal = 0;

    plugin = (d3h_plugin_t *)calloc(1, sizeof(d3h_plugin_t));
    plugin->label = "pydaw";
    dll = (d3h_dll_t *)calloc(1, sizeof(d3h_dll_t));
    dll->name = "pydaw";
    dll->descfn = (PYFX_Descriptor_Function)PYFX_descriptor;
    j = 0;

    plugin->descriptor = PYFX_descriptor(0);

    plugin->dll = dll;

    /* Count number of i/o buffers and ports required */
    plugin->ins = 0;
    plugin->outs = 2;
    plugin->controlIns = 0;
    plugin->controlOuts = 0;

    /* set up instances */

    this_instance = (d3h_instance_t*)malloc(sizeof(d3h_instance_t));
    this_instance->plugin = plugin;
    this_instance->friendly_name = "pydaw";

    insTotal += plugin->ins;
    outsTotal += plugin->outs;
    controlInsTotal += plugin->controlIns;
    controlOutsTotal += plugin->controlOuts;

    //pluginInputBuffers = (float **)malloc(insTotal * sizeof(float *));
    pluginOutputBuffers = (float **)malloc(outsTotal * sizeof(float *));

    instanceHandles = (PYFX_Handle *)malloc(sizeof(PYFX_Handle));

    sample_rate = 44100.0f;


    /*Initialize Portaudio*/
    PaStreamParameters inputParameters, outputParameters;
    PaStream *stream;
    PaError err;
    err = Pa_Initialize();
    //if( err != paNoError ) goto error;
    /* default input device */
    inputParameters.device = Pa_GetDefaultInputDevice();

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


        in = 0;
    out = 0;

    for (j = 0; j < this_instance->plugin->ins; ++j)
    {
        lmalloc((void**)(&pluginInputBuffers[in]),
            (sizeof(float) * FRAMES_PER_BUFFER));

        int f_i = 0;
        while(f_i < FRAMES_PER_BUFFER)
        {
            pluginInputBuffers[in][f_i] = 0.0f;
            f_i++;
        }
        ++in;
    }
    for (j = 0; j < this_instance->plugin->outs; ++j)
    {
        buffer_alloc((void**)(&pluginOutputBuffers[out]),
            (sizeof(float) * FRAMES_PER_BUFFER));

        int f_i = 0;
        while(f_i < FRAMES_PER_BUFFER)
        {
            pluginOutputBuffers[out][f_i] = 0.0f;
            f_i++;
        }

        ++out;
    }


    /* Instantiate plugins */

    plugin = this_instance->plugin;
    instanceHandles = g_pydaw_instantiate(plugin->descriptor, sample_rate);
    if (!instanceHandles)
    {
        printf("\nError: Failed to instantiate PyDAW\n");
        return 1;
    }

    /* Create OSC thread */

    serverThread = lo_server_thread_new("19271", osc_error);
    lo_server_thread_add_method(serverThread, NULL, NULL, osc_message_handler,
            NULL);
    lo_server_thread_start(serverThread);

    /* Connect and activate plugins */

    in = out = controlIn = controlOut = 0;

    plugin = this_instance->plugin;

    for (j = 0; j < 2; j++)
    {
        v_pydaw_connect_port(instanceHandles, j, pluginOutputBuffers[out++]);
    }

    assert(in == insTotal);
    assert(out == outsTotal);
    assert(controlIn == controlInsTotal);
    assert(controlOut == controlOutsTotal);


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
                char * f_key_char = c_iterate_2d_char_array(f_current_string);
                if(f_current_string->eof)
                {
                    break;
                }
                if(!strcmp(f_key_char, "") || f_current_string->eol)
                {
                    continue;
                }

                char * f_value_char = c_iterate_2d_char_array_to_next_line(
                        f_current_string);

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
                }
                else
                {
                    printf("Unknown key|value pair: %s|%s\n", f_key_char,
                            f_value_char);
                }
            }

            g_free_2d_char_array(f_current_string);

            int f_device_result = midiDeviceInit(
                &MIDI_DEVICE, f_midi_device_name);

            if(f_device_result == 1)
            {
                f_failure_count++;
                sprintf(f_cmd_buffer, "%s \"%s %s\"", f_show_dialog_cmd,
                        "Error: did not find MIDI device:",
                        f_midi_device_name);
                system(f_cmd_buffer);
                continue;
            }
            else if(f_device_result == 2)
            {
                f_failure_count++;
                sprintf(f_cmd_buffer, "%s \"%s %s, %s\"", f_show_dialog_cmd,
                        "Error opening MIDI device: ",
                        f_midi_device_name, Pm_GetErrorText(f_midi_err));
                system(f_cmd_buffer);
                continue;
            }

            f_with_midi = 1;

        }
        else
        {
            f_failure_count++;
            printf("%s does not exist, running %s\n", f_device_file_path,
                    f_show_dialog_cmd);
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
        inputParameters.channelCount = 0;
        inputParameters.sampleFormat = PA_SAMPLE_TYPE;
        inputParameters.suggestedLatency =
                Pa_GetDeviceInfo(inputParameters.device )->
                defaultLowInputLatency;
        inputParameters.hostApiSpecificStreamInfo = NULL;

        if (outputParameters.device == paNoDevice)
        {
          sprintf(f_cmd_buffer, "%s \"%s\"", f_show_dialog_cmd,
                  "Error: No default output device.");
          system(f_cmd_buffer);
          continue;
        }

        outputParameters.channelCount = 2; /* stereo output */
        outputParameters.sampleFormat = PA_SAMPLE_TYPE;
        outputParameters.suggestedLatency =
                Pa_GetDeviceInfo(outputParameters.device )->
                defaultLowOutputLatency;
        outputParameters.hostApiSpecificStreamInfo = NULL;

        int f_i = 0;
        int f_found_index = 0;
        while(f_i < Pa_GetDeviceCount())
        {
            const PaDeviceInfo * f_padevice = Pa_GetDeviceInfo(f_i);
            if(!strcmp(f_padevice->name, f_device_name))
            {
                outputParameters.device = f_i;
                f_found_index = 1;
                break;
            }
            f_i++;
        }

        if(!f_found_index)
        {
            sprintf(f_cmd_buffer,
                    "%s \"Did not find device '%s' on this system.\"",
                    f_show_dialog_cmd, f_device_name);
            system(f_cmd_buffer);
            f_failure_count++;
            continue;
        }

        err = Pa_OpenStream(
                  &stream,
                  0, //&inputParameters,
                  &outputParameters,
                  sample_rate, //SAMPLE_RATE,
                  f_frame_count, //FRAMES_PER_BUFFER,
                  /* we won't output out of range samples so don't bother
                   * clipping them */
                  0, /* paClipOff, */
                  portaudioCallback,
                  NULL );
        if( err != paNoError )
        {
            f_failure_count++;
            sprintf(f_cmd_buffer, "%s \"%s %s\"", f_show_dialog_cmd,
                    "Error while opening audio device: ", Pa_GetErrorText(err));
            system(f_cmd_buffer);
            continue;
        }
        break;
    }

    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    signal(SIGHUP, signalHandler);
    signal(SIGQUIT, signalHandler);
    pthread_sigmask(SIG_UNBLOCK, &_signals, 0);

    v_pydaw_activate(instanceHandles, f_thread_count, f_thread_affinity,
            argv[2]);

    v_queue_osc_message("ready", "");

    // only for no-hardware mode
    float * f_portaudio_input_buffer;
    float * f_portaudio_output_buffer;

    exiting = 0;
    if(!PYDAW_NO_HARDWARE)
    {
        err = Pa_StartStream(stream);
        if(err != paNoError)
        {
            sprintf(f_cmd_buffer, "%s \"%s\"", f_show_dialog_cmd,
                    "Error: Unknown error while starting device.  Please "
                    "re-configure your device and try starting PyDAW again.");
            system(f_cmd_buffer);
            exiting = 1;
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

    assert(0);  // TODO:  close the MIDI devices

    if(!PYDAW_NO_HARDWARE)
    {
        err = Pa_CloseStream( stream );
        Pa_Terminate();
        Pm_Terminate();
    }
    v_pydaw_cleanup(instanceHandles);

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

    printf("PyDAW main() returning\n\n\n");
    return 0;
}

void osc_error(int num, const char *msg, const char *path)
{
    printf("liblo server error %d in path %s: %s\n", num, path, msg);
}

int osc_configure_handler(d3h_instance_t *instance, lo_arg **argv)
{
    const char *key = (const char *)&argv[0]->s;
    const char *value = (const char *)&argv[1]->s;

    v_pydaw_parse_configure_message(pydaw_data, key, value);

    return 0;
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
        f_i++;
    }

    return 1;
}

int osc_message_handler(const char *path, const char *types, lo_arg **argv,
                        int argc, void *data, void *user_data)
{
    if(!strcmp(path, "/musikernel/configure") && !strcmp(types, "ss"))
    {
        return osc_configure_handler(this_instance, argv);
    }
    else
    {
        return osc_debug_handler(path, types, argv, argc, data, user_data);
    }
}


void v_pydaw_parse_configure_message(t_pydaw_data* self,
        const char* a_key, const char* a_value)
{
    printf("v_pydaw_parse_configure_message:  key: \"%s\", value: \"%s\"\n",
            a_key, a_value);
    if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 3,
                PYDAW_TINY_STRING);

        int f_plugin_uid = atoi(f_val_arr->array[0]);

        int f_port = atoi(f_val_arr->array[1]);
        float f_value = atof(f_val_arr->array[2]);

        t_pydaw_plugin * f_instance;
        pthread_spin_lock(&self->main_lock);

        f_instance = self->plugin_pool[f_plugin_uid];

        if(f_instance)
        {
            f_instance->descriptor->set_port_value(
                f_instance->PYFX_handle, f_port, f_value);
        }
        else
        {
            printf("Error, no valid plugin instance\n");
        }
        pthread_spin_unlock(&self->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_CONFIGURE_PLUGIN))
    {
        t_1d_char_array * f_val_arr = c_split_str_remainder(a_value, '|', 3,
                PYDAW_LARGE_STRING);
        int f_plugin_uid = atoi(f_val_arr->array[0]);
        char * f_key = f_val_arr->array[1];
        char * f_message = f_val_arr->array[2];

        t_pydaw_plugin * f_instance = self->plugin_pool[f_plugin_uid];

        if(f_instance)
        {
            f_instance->descriptor->configure(
                f_instance->PYFX_handle, f_key, f_message, &self->main_lock);
        }
        else
        {
            printf("Error, no valid plugin instance\n");
        }

        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_PER_AUDIO_ITEM_FX))
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 4,
                PYDAW_SMALL_STRING);
        int f_region_uid = atoi(f_arr->array[0]);
        int f_item_index = atoi(f_arr->array[1]);
        int f_port_num = atoi(f_arr->array[2]);
        float f_port_val = atof(f_arr->array[3]);

        v_paif_set_control(self, f_region_uid, f_item_index,
                f_port_num, f_port_val);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_PLAY)) //Begin playback
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 2,
                PYDAW_SMALL_STRING);
        int f_region = atoi(f_arr->array[0]);
        int f_bar = atoi(f_arr->array[1]);
        v_set_playback_mode(self, 1, f_region, f_bar, 1);
        g_free_1d_char_array(f_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_REC)) //Begin recording
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 2,
                PYDAW_SMALL_STRING);
        int f_region = atoi(f_arr->array[0]);
        int f_bar = atoi(f_arr->array[1]);
        v_set_playback_mode(self, 2, f_region, f_bar, 1);
        g_free_1d_char_array(f_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_STOP))
    {
        v_set_playback_mode(self, 0, -1, -1, 1);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SR))
    {
        //Ensure that a project isn't being loaded right now
        pthread_spin_lock(&self->main_lock);
        pthread_spin_unlock(&self->main_lock);

        int f_uid = atoi(a_value);
        t_pyregion * f_result = g_pyregion_get(self, f_uid);
        int f_region_index = i_get_song_index_from_region_uid(self, f_uid);

        if(f_region_index >= 0 )
        {
            t_pyregion * f_old_region = NULL;
            if(self->pysong->regions[f_region_index])
            {
                f_old_region = self->pysong->regions[f_region_index];
            }
            pthread_spin_lock(&self->main_lock);
            self->pysong->regions[f_region_index] = f_result;
            pthread_spin_unlock(&self->main_lock);
            if(f_old_region)
            {
                free(f_old_region);
            }
        }
        else
        {
            printf("region %i is not in song, not loading...", f_uid);
        }
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SI)) //Save Item
    {
        pthread_spin_lock(&self->main_lock);
        g_pyitem_get(self, atoi(a_value));
        pthread_spin_unlock(&self->main_lock);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SS))  //Save Song
    {
        g_pysong_get(self, 1);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SAVE_ATM))
    {
        int f_uid = atoi(a_value);
        t_pydaw_atm_region * f_result = g_atm_region_get(self, f_uid);
        int f_region_index = i_get_song_index_from_region_uid(self, f_uid);

        if(f_region_index >= 0 )
        {
            t_pydaw_atm_region * f_old_region = NULL;
            if(self->pysong->regions_atm[f_region_index])
            {
                f_old_region = self->pysong->regions_atm[f_region_index];
            }
            pthread_spin_lock(&self->main_lock);
            self->pysong->regions_atm[f_region_index] = f_result;
            pthread_spin_unlock(&self->main_lock);
            if(f_old_region)
            {
                v_atm_region_free(f_old_region);
            }
        }
        else
        {
            printf("region %i is not in song, not loading...", f_uid);
        }
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_AUDIO_ITEM_LOAD_ALL))
    {
        int f_uid = atoi(a_value);
        //t_pydaw_audio_items * f_old;
        t_pydaw_audio_items * f_result = v_audio_items_load_all(self,
                f_uid);
        int f_region_index = i_get_song_index_from_region_uid(self,
                f_uid);
        pthread_spin_lock(&self->main_lock);
        self->pysong->audio_items[f_region_index] = f_result;
        pthread_spin_unlock(&self->main_lock);
        //v_pydaw_audio_items_free(f_old); //Method needs to be re-thought...
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_PER_AUDIO_ITEM_FX_REGION))
    {
        int f_uid = atoi(a_value);
        t_pydaw_per_audio_item_fx_region * f_result =
                g_paif_region_open(self, f_uid);
        int f_region_index = i_get_song_index_from_region_uid(self,
                f_uid);
        t_pydaw_per_audio_item_fx_region * f_old =
                self->pysong->per_audio_item_fx[f_region_index];
        pthread_spin_lock(&self->main_lock);
        self->pysong->per_audio_item_fx[f_region_index] = f_result;
        pthread_spin_unlock(&self->main_lock);
        v_paif_region_free(f_old);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_ADD_TO_WAV_POOL))
    {
        t_key_value_pair * f_kvp = g_kvp_get(a_value);
        printf("v_wav_pool_add_item(self->wav_pool, %i, \"%s\")\n",
                atoi(f_kvp->key), f_kvp->value);
        v_wav_pool_add_item(self->wav_pool, atoi(f_kvp->key),
                f_kvp->value);
        free(f_kvp);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_LOOP)) //Set loop mode
    {
        int f_value = atoi(a_value);

        pthread_spin_lock(&self->main_lock);
        v_set_loop_mode(self, f_value);
        pthread_spin_unlock(&self->main_lock);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_OS)) //Open Song
    {
        t_key_value_pair * f_kvp = g_kvp_get(a_value);
        int f_first_open = atoi(f_kvp->key);
        v_open_project(self, f_kvp->value, f_first_open);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_TEMPO)) //Change tempo
    {
        pthread_spin_lock(&self->main_lock);
        v_set_tempo(self, atof(a_value));
        pthread_spin_unlock(&self->main_lock);
        //To reload audio items when tempo changed
        //g_pysong_get(self);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SOLO)) //Set track solo
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_mode = atoi(f_val_arr->array[1]);
        assert(f_mode == 0 || f_mode == 1);

        pthread_spin_lock(&self->main_lock);

        self->track_pool_all[f_track_num]->solo = f_mode;
        //self->track_pool_all[f_track_num]->period_event_index = 0;

        v_pydaw_set_is_soloed(self);

        pthread_spin_unlock(&self->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_MUTE)) //Set track mute
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_mode = atoi(f_val_arr->array[1]);
        assert(f_mode == 0 || f_mode == 1);
        pthread_spin_lock(&self->main_lock);

        self->track_pool_all[f_track_num]->mute = f_mode;
        //self->track_pool_all[f_track_num]->period_event_index = 0;

        pthread_spin_unlock(&self->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_UPDATE_AUDIO_INPUTS))
    {
        v_pydaw_update_audio_inputs(self);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_CHANGE_INSTRUMENT))
    {
        //Ensure that a project isn't being loaded right now
        pthread_spin_lock(&self->main_lock);
        pthread_spin_unlock(&self->main_lock);

        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_TINY_STRING);
        assert(0);
        //int f_track_num = atoi(f_val_arr->array[0]);
        //int f_plugin_index = atoi(f_val_arr->array[1]);
        //v_set_plugin_index(self,
        //    self->track_pool_all[f_track_num], f_plugin_index, 1);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_PREVIEW_SAMPLE))
    {
        v_pydaw_set_preview_file(self, a_value);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_PLUGIN_INDEX))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 5,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_index = atoi(f_val_arr->array[1]);
        int f_plugin_index = atoi(f_val_arr->array[2]);
        int f_plugin_uid = atoi(f_val_arr->array[3]);
        int f_power = atoi(f_val_arr->array[4]);

        v_pydaw_set_plugin_index(
            self, f_track_num, f_index,
            f_plugin_index, f_plugin_uid, f_power, 1);

        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_UPDATE_SEND))
    {
        v_pydaw_update_track_send(self, 1);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SEND_VOL))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 3,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_index = atoi(f_val_arr->array[1]);
        int f_vol = atof(f_val_arr->array[2]);

        v_pydaw_update_send_vol(self, f_track_num, f_index, f_vol);


        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SET_OVERDUB_MODE))
    {
        int f_bool = atoi(a_value);
        assert(f_bool == 0 || f_bool == 1);
        pthread_spin_lock(&self->main_lock);
        self->overdub_mode = f_bool;
        pthread_spin_unlock(&self->main_lock);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_LOAD_CC_MAP))
    {
        t_1d_char_array * f_val_arr = c_split_str_remainder(a_value, '|', 2,
                PYDAW_SMALL_STRING);
        int f_plugin_uid = atoi(f_val_arr->array[0]);
        pydaw_data->plugin_pool[f_plugin_uid]->descriptor->set_cc_map(
            pydaw_data->plugin_pool[f_plugin_uid]->PYFX_handle,
            f_val_arr->array[1]);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_LOAD_AB_OPEN))
    {
        v_pydaw_set_ab_file(self, a_value);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_LOAD_AB_SET))
    {
        int f_mode = atoi(a_value);
        v_pydaw_set_ab_mode(self, f_mode);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_WE_SET))
    {
        v_pydaw_set_wave_editor_item(self, a_value);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_PANIC))
    {
        pthread_spin_lock(&self->main_lock);
        self->is_offline_rendering = 1;
        pthread_spin_unlock(&self->main_lock);

        v_pydaw_panic(self);

        pthread_spin_lock(&self->main_lock);
        self->is_offline_rendering = 0;
        pthread_spin_unlock(&self->main_lock);

    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SET_POS))
    {
        if(self->playback_mode != 0)
        {
            return;
        }
        t_1d_char_array * f_val_arr =
            c_split_str(a_value, '|', 2, PYDAW_TINY_STRING);
        int f_region = atoi(f_val_arr->array[0]);
        int f_bar = atoi(f_val_arr->array[1]);

        pthread_spin_lock(&self->main_lock);
        v_set_playback_cursor(self, f_region, f_bar);
        pthread_spin_unlock(&self->main_lock);

        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_RATE_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(PYDAW_SMALL_STRING);
        char f_tmp_char[PYDAW_SMALL_STRING];
        sprintf(f_tmp_char, "%s", a_value);
        f_arr->array = f_tmp_char;
        char * f_in_file = c_iterate_2d_char_array(f_arr);
        char * f_out_file = c_iterate_2d_char_array(f_arr);
        char * f_start_str = c_iterate_2d_char_array(f_arr);
        char * f_end_str = c_iterate_2d_char_array(f_arr);
        float f_start = atof(f_start_str);
        float f_end = atof(f_end_str);

        v_pydaw_rate_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);
        free(f_start_str);
        free(f_end_str);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_PITCH_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(PYDAW_SMALL_STRING);
        char f_tmp_char[PYDAW_SMALL_STRING];
        sprintf(f_tmp_char, "%s", a_value);
        f_arr->array = f_tmp_char;
        char * f_in_file = c_iterate_2d_char_array(f_arr);
        char * f_out_file = c_iterate_2d_char_array(f_arr);
        char * f_start_str = c_iterate_2d_char_array(f_arr);
        char * f_end_str = c_iterate_2d_char_array(f_arr);
        float f_start = atof(f_start_str);
        float f_end = atof(f_end_str);

        v_pydaw_pitch_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);
        free(f_start_str);
        free(f_end_str);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_GLUE_AUDIO_ITEMS))
    {
        t_pydaw_line_split * f_val_arr = g_split_line('|', a_value);
        char * f_path = f_val_arr->str_arr[0];  //Don't free this
        int f_region_index = atoi(f_val_arr->str_arr[1]);
        int f_start_bar = atoi(f_val_arr->str_arr[2]);
        int f_end_bar = atoi(f_val_arr->str_arr[3]);
        int f_i = 0;
        while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
        {
            self->audio_glue_indexes[f_i] = 0;
            f_i++;
        }

        f_i = 4;
        while(f_i < f_val_arr->count)
        {
            int f_index = atoi(f_val_arr->str_arr[f_i]);
            self->audio_glue_indexes[f_index] = 1;
            f_i++;
        }

        v_pydaw_offline_render(self, f_region_index, f_start_bar,
                f_region_index, f_end_bar, f_path, 1);

        v_free_split_line(f_val_arr);

    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_WAVPOOL_ITEM_RELOAD))
    {
        int f_uid = atoi(a_value);
        t_wav_pool_item * f_old =
                g_wav_pool_get_item_by_uid(self->wav_pool, f_uid);
        t_wav_pool_item * f_new =
                g_wav_pool_item_get(f_uid, f_old->path,
                self->wav_pool->sample_rate);

        float * f_old_samples[2];
        f_old_samples[0] = f_old->samples[0];
        f_old_samples[1] = f_old->samples[1];

        pthread_spin_lock(&self->main_lock);

        f_old->channels = f_new->channels;
        f_old->length = f_new->length;
        f_old->ratio_orig = f_new->ratio_orig;
        f_old->sample_rate = f_new->sample_rate;
        f_old->samples[0] = f_new->samples[0];
        f_old->samples[1] = f_new->samples[1];

        pthread_spin_unlock(&self->main_lock);

        if(f_old_samples[0])
        {
            free(f_old_samples[0]);
        }

        if(f_old_samples[1])
        {
            free(f_old_samples[1]);
        }

        free(f_new);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_MASTER_VOL))
    {
        MASTER_VOL = atof(a_value);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_EXIT))
    {
        exiting = 1;
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_MIDI_LEARN))
    {
        pydaw_data->midi_learn = 1;
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_MIDI_DEVICE))
    {
        t_pydaw_line_split * f_val_arr = g_split_line('|', a_value);
        int f_on = atoi(f_val_arr->str_arr[0]);
        int f_device = atoi(f_val_arr->str_arr[1]);
        int f_output = atoi(f_val_arr->str_arr[2]);
        v_free_split_line(f_val_arr);

        pthread_spin_lock(&self->main_lock);

        v_pydaw_set_midi_device(pydaw_data, f_on, f_device, f_output);

        pthread_spin_unlock(&self->main_lock);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_WE_EXPORT))
    {
        v_pydaw_we_export(self, a_value);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_STOP_PREVIEW))
    {
        if(self->is_previewing)
        {
            pthread_spin_lock(&self->main_lock);
            v_adsr_release(self->preview_audio_item->adsr);
            pthread_spin_unlock(&self->main_lock);
        }
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_KILL_ENGINE))
    {
        assert(0);
    }
    else
    {
        printf("Unknown configure message key: %s, value %s\n", a_key, a_value);
    }
}


