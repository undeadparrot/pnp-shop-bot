from setuptools import setup, find_packages

setup(
    name='pnp-shop-bot',
    version='1.1.0',
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot',
        'pytest'
    ],
    entry_points={
        'console_scripts': [
            'pnp_shop_bot=pnp_shop_bot.app:main',
            'pnp_shop_bot_initialize=pnp_shop_bot.db:initialize'
        ]
    }
)

