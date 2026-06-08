import os
import json
import logging
import tempfile
import shutil

LOG = logging.getLogger("generic")


class ConfigPersistence:
    '''
    Manages config state and persistence.
    '''
    def __init__(self, config_model_cls, config_file):
        self.config_file = config_file
        self.config_model_cls = config_model_cls
        self.first_run = not os.path.exists(config_file)
        self._config = self.load()

    def load(self):
        '''
        Load config from file
        '''
        if not os.path.exists(self.config_file):
            return self.config_model_cls()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as outfile:
                config = json.load(outfile)
            instance = self.config_model_cls(**config)
            return instance

        except (json.JSONDecodeError, ValueError) as e:
            LOG.error(f"Failed to load config from {self.config_file}: {e}")
            LOG.warning("Falling back to default configuration. Your config file may be corrupted.")

            # Fall back to default config
            return self.config_model_cls()

        except Exception as e:
            LOG.error(f"Unexpected error loading config: {e}")
            return self.config_model_cls()

    def save(self):
        '''
        Write configuration to file using atomic write pattern
        '''
        config_dir = os.path.dirname(self.config_file)
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        LOG.debug("Writing config")

        try:
            # Write to temporary file in same directory (for atomic rename)
            fd, temp_path = tempfile.mkstemp(
                dir=config_dir,
                prefix='.config_',
                suffix='.json.tmp'
            )

            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as outfile:
                    json.dump(
                        self._config.dict(),
                        outfile,
                        indent='\t',
                        separators=(',', ': ')
                    )

                # Atomic rename (only succeeds if write completed)
                # On POSIX systems, this is atomic - the file is replaced instantly
                # If the process crashes before this line, original config.json is untouched
                shutil.move(temp_path, self.config_file)
                LOG.debug("Config saved successfully")

            except Exception:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise

        except Exception as e:
            LOG.error(f"Failed to save config: {e}")
            raise

    def get_config(self):
        return self._config
