FROM odoo:19

USER root

# System packages for common Odoo dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        libldap2-dev \
        libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy custom addons
COPY addons/ /mnt/extra-addons/addons/
COPY third-party/ /mnt/extra-addons/third-party/

# Copy Odoo config
COPY config/odoo.conf /etc/odoo/odoo.conf

# Fix ownership
RUN chown -R odoo:odoo /mnt/extra-addons /etc/odoo/odoo.conf

USER odoo
