
class AbstractIPC:
    """ Abstract class containing the minimum contract for a
        host to run MK Plugins
    """
    def __init__(self):
        pass

    def pydaw_update_plugin_control(self, a_plugin_uid, a_port, a_val):
        raise NotImplementedError

    def pydaw_configure_plugin(self, a_plugin_uid, a_key, a_message):
        raise NotImplementedError

    def pydaw_midi_learn(self):
        raise NotImplementedError

    def pydaw_load_cc_map(self, a_plugin_uid, a_str):
        raise NotImplementedError

class AbstractProject:
    def __init__(self):
        self.plugin_pool_folder = None

    def save_file(a_plugins_folder, a_plugin_uid, a_file):
        raise NotImplementedError

    def commit(self, a_message):
        raise NotImplementedError

    def flush_history(self):
        raise NotImplementedError
