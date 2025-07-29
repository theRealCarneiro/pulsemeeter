import os
import json
import logging

LOG = logging.getLogger("generic")


class ConfigPersistence:
    '''
    Manages config state and persistence.
    '''
    def __init__(self, config_model_cls, config_file):
        self.config_file = config_file
        self.config_model_cls = config_model_cls
        self._config = self.load()

    def load(self):
        '''
        Load config from file
        '''
        if not os.path.exists(self.config_file):
            return self.config_model_cls()

        with open(self.config_file, 'r', encoding='utf-8') as outfile:
            config = json.load(outfile)

        instance = self.config_model_cls(**config)
        return instance

    def save(self):
        '''
        Write configuration to file
        '''
        config_dir = os.path.dirname(self.config_file)
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        LOG.debug("Writing config")
        with open(self.config_file, 'w', encoding='utf-8') as outfile:
            json.dump(self.get_config().dict(), outfile, indent='\t', separators=(',', ': '))

    def get_config(self):
        return self._config
