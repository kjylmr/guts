#!/usr/bin/env bash
# Plugin file for guts services
# -------------------------------

# Dependencies:
# ``functions`` file
# ``DEST``, ``DATA_DIR``, ``STACK_USER`` must be defined

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

# Support entry points installation of console scripts
if [[ -d $GUTS_DIR/bin ]]; then
    GUTS_BIN_DIR=$GUTS_DIR/bin
else
    GUTS_BIN_DIR=$(get_python_exec_prefix)
fi


# Functions
# ---------

# cleanup_guts() - Remove residual data files, anything left over from previous
# runs that a clean run would need to clean up
function cleanup_guts {
    sudo rm -rf $GUTS_AUTH_CACHE_DIR $GUTS_AUTH_CACHE_DIR $GUTS_STATE_PATH
}


function configure_guts_rpc_backend() {
    # Configure the rpc service.
    iniset_rpc_backend guts $GUTS_CONF

    # Set non-default rabbit virtual host if required.
    if [[ -n "$GUTS_RABBIT_VHOST" ]]; then
        iniset $GUTS_CONF DEFAULT rabbit_virtual_host $GUTS_RABBIT_VHOST
        iniset $GUTS_CONF rabbitmq virtual_host $GUTS_RABBIT_VHOST
    fi
}


# Entry points
# ------------

# configure_guts() - Set config files, create data dirs, etc
function configure_guts {
    sudo install -d -o $STACK_USER -m 755 $GUTS_CONF_DIR

    cp -p $GUTS_DIR/etc/guts/policy.json $GUTS_CONF_DIR
    rm -f $GUTS_CONF

    configure_rootwrap guts

    cp $GUTS_DIR/etc/guts/api-paste.ini $GUTS_API_PASTE_INI

    # Setup Default section
    iniset $GUTS_CONF DEFAULT graceful_shutdown_timeout $GRACEFUL_SHUTDOWN_TIMEOUT
    iniset $GUTS_CONF DEFAULT os_privileged_user_tenant $SERVICE_TENANT_NAME
    iniset $GUTS_CONF DEFAULT os_privileged_user_password $SERVICE_PASSWORD
    iniset $GUTS_CONF DEFAULT os_privileged_user_name nova
    iniset $GUTS_CONF DEFAULT glance_api_servers "http://${KEYSTONE_AUTH_HOST}:9292"
    iniset $GUTS_CONF DEFAULT osapi_migration_workers $GUTS_OSAPI_MIGRATION_WORKERS
    iniset $GUTS_CONF DEFAULT migration_clear zero
    iniset $GUTS_CONF DEFAULT rpc_backend rabbit
    iniset $GUTS_CONF DEFAULT os_region_name $REGION_NAME
    iniset $GUTS_CONF DEFAULT enable_v1_api true
    iniset $GUTS_CONF DEFAULT periodic_interval $GUTS_PERIODIC_INTERVAL
    iniset $GUTS_CONF DEFAULT osapi_migration_listen "0.0.0.0"
    iniset $GUTS_CONF DEFAULT osapi_migration_extension "guts.api.contrib.standard_extensions"
    iniset $GUTS_CONF DEFAULT rootwrap_config "$GUTS_CONF_DIR/rootwrap.conf"
    iniset $GUTS_CONF DEFAULT api_paste_config $GUTS_API_PASTE_INI
    iniset $GUTS_CONF DEFAULT iscsi_helper $GUTS_ISCSI_HELPER
    iniset $GUTS_CONF DEFAULT debug $GUTS_DEBUG
    iniset $GUTS_CONF DEFAULT nova_catalog_info $GUTS_NOVA_CATALOG_INFO
    iniset $GUTS_CONF DEFAULT nova_catalog_admin_info $GUTS_NOVA_CATALOG_ADMIN_INFO
    iniset $GUTS_CONF DEFAULT auth_strategy keystone

    # configure the database.
    iniset $GUTS_CONF database connection `database_connection_url guts`

    inicomment $GUTS_API_PASTE_INI filter:authtoken auth_host
    inicomment $GUTS_API_PASTE_INI filter:authtoken auth_port
    inicomment $GUTS_API_PASTE_INI filter:authtoken auth_protocol
    inicomment $GUTS_API_PASTE_INI filter:authtoken cafile
    inicomment $GUTS_API_PASTE_INI filter:authtoken admin_tenant_name
    inicomment $GUTS_API_PASTE_INI filter:authtoken admin_user
    inicomment $GUTS_API_PASTE_INI filter:authtoken admin_password
    inicomment $GUTS_API_PASTE_INI filter:authtoken signing_dir

    configure_auth_token_middleware $GUTS_CONF guts $GUTS_AUTH_CACHE_DIR

    # Configure keystone auth url
    iniset $GUTS_CONF_FILE keystone auth_url "http://${KEYSTONE_AUTH_HOST}:5000/v2.0"

    # Configure Guts API URL
    iniset $GUTS_CONF_FILE guts url "http://127.0.0.1:7000"

    # configure rpc backend
    configure_guts_rpc_backend

    if is_fedora || is_suse; then
        # guts defaults to /usr/local/bin, but fedora and suse pip like to
        # install things in /usr/bin
        iniset $GUTS_CONF DEFAULT bindir "/usr/bin"
    fi

    if [ -n "$GUTS_STATE_PATH" ]; then
        iniset $GUTS_CONF DEFAULT state_path "$GUTS_STATE_PATH"
        iniset $GUTS_CONF oslo_concurrency lock_path "$GUTS_STATE_PATH"
    fi

    if [ "$SYSLOG" != "False" ]; then
        iniset $NOVA_CONF DEFAULT use_syslog "True"
    fi

    # Format logging
    if [ "$LOG_COLOR" == "True" ] && [ "$SYSLOG" == "False" ] && [ "$GUTS_USE_MOD_WSGI" == "False" ]  ; then
        setup_colorized_logging $GUTS_CONF DEFAULT
    else
        # Show user_name and project_name instead of user_id and project_id
        iniset $GUTS_CONF DEFAULT logging_context_format_string "%(asctime)s.%(msecs)03d %(levelname)s %(name)s [%(request_id)s %(user_name)s %(project_name)s] %(instance)s%(message)s"
    fi
    if [ "$GUTS_USE_MOD_WSGI" == "True" ]; then
        _config_guts_apache_wsgi
    fi
}


# create_guts_accounts() - Set up common required guts accounts
#
# Tenant      User       Roles
# ------------------------------
# service     guts       admin
function create_guts_accounts {
    if [[ "$ENABLED_SERVICES" =~ "gu-api" ]]; then

        create_service_user "guts" "admin"

        if [[ "$KEYSTONE_CATALOG_BACKEND" = 'sql' ]]; then
            local guts_api_url
            guts_api_url="$GUTS_SERVICE_PROTOCOL://$GUTS_SERVICE_HOST:$GUTS_SERVICE_PORT"

            get_or_create_service "guts" "migration" "OpenStack Migration Service"
            get_or_create_endpoint "migration" \
                "$REGION_NAME" \
                "$guts_api_url/v1/\$(tenant_id)s" \
                "$guts_api_url/v1/\$(tenant_id)s" \
                "$guts_api_url/v1/\$(tenant_id)s"
        fi
    fi
}


# create_nova_cache_dir() - Part of the init_nova() process
function create_guts_cache_dir {
    # Create cache dir
    sudo install -d -o $STACK_USER $GUTS_AUTH_CACHE_DIR
    rm -f $GUTS_AUTH_CACHE_DIR/*
}

# init_guts() - Initialize databases, etc.
function init_guts() {
    # (re)create Guts database
    recreate_database guts utf8

    $GUTS_BIN_DIR/guts-manage db sync
    create_guts_cache_dir
}


# install_guts() - Collect source and prepare
function install_guts() {
    install_guts_pythonclient

    git_clone $GUTS_REPO $GUTS_DIR $GUTS_BRANCH
    setup_package $GUTS_DIR -e
}


function install_guts_pythonclient() {
    git_clone $GUTS_PYTHONCLIENT_REPO $GUTS_PYTHONCLIENT_DIR $GUTS_PYTHONCLIENT_BRANCH
    setup_package $GUTS_PYTHONCLIENT_DIR -e
}


# start_guts() - Start running processes, including screen
function start_guts() {
    screen_it gu-api "cd $GUTS_DIR && $GUTS_BIN_DIR/guts-api --config-file $GUTS_CONF"
    screen_it gu-migration "cd $GUTS_DIR && $GUTS_BIN_DIR/guts-migration --config-file $GUTS_CONF"
}


# stop_guts() - Stop running processes
function stop_guts() {
    # Kill the Guts screen windows
    for service in gu-api gu-migration; do
        screen -S $SCREEN_NAME -p $service -X kill
    done
}


function cleanup_guts() {

    # Cleanup keystone signing dir
    sudo rm -rf $GUTS_STATE_PATH $GUTS_AUTH_CACHE_DIR
}


# check for service enabled
if is_service_enabled guts; then

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        # Perform installation of service source
        echo_summary "Installing Guts"
        install_guts

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Guts"
        configure_guts
        echo_summary "Creating Guts entities for auth service"
        create_guts_accounts

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Guts"
        init_guts
        echo_summary "Starting Guts"
        start_guts

        # Give Guts some time to Start
        sleep 3
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_guts
        cleanup_guts
    fi
fi


# Restore xtrace
$XTRACE
