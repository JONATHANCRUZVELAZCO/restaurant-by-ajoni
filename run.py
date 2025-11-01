import os
from app import create_app

env = os.getenv('FLASK_ENV', 'production')
config_name = 'production' if env == 'production' else 'development'

app = create_app(config_name)


if __name__ == '__main__':
    # For local testing
    port = int(os.getenv('PORT', '5000'))
    debug = app.config.get('DEBUG', False)
    app.run(host='0.0.0.0', port=port, debug=debug)
