# GUTS Demo Instructions

## Prerequisite

### SSH Access
    
Login to these environments, from you local machine. Verify that your private key is working. Also keep these login sessions open in separate terminal.

#### Login to Guts Environment

From you local machine, login to guts environment ( Machine where guts api, scheduler and migration service is running) because we can’t have public ip to this machine, we need to access this machine through another machine named source.

`ssh ubuntu@180.148.27.171`

From inside that machine ssh to guts-environment by running

`ssh -i ~/.ssh/bala.key stack@192.168.100.25`

No need to source openrc, it is already sourced. Run some sample commands. Verify some openstack commands.

```
openstack user list
guts service-list
guts resource-list
```

You will see two services running ( migration & scheduler) and no resources.

#### Login to Destination Environment

`ssh ubuntu@180.148.27.190`

And then verify again that there are no instances booted on destination.

```
openstack image list
openstack server list
```

### UI Access

Similarly in a browser, open these urls, in different tabs and remain logged in.

#### Destination Environment Dashboard

    Url :              http://180.148.27.190/dashboard/
    Username :         admin
    Password :         secret

Verify environment where we will migrate.
There shouldn’t be any machines running to save resources.
Sample keypairs, secgroups & flavor are there.

#### Guts Dashboard

    Url:               http://180.148.27.191:8888/guts/migrations/
    Username:          admin
    Password :         secret

After login , verify there is no current migration and source and destination.
We will add one source and one destination from command line first later as part of demo.

### vSphere

Make sure you are logged into vSphere and verify one sample folder created inside VM which will be migrated.
Make sure vm to be migrated is in terminated state.

## Demo Steps

From Terminal of guts-environment

From the earlier step, switch to terminal where you have ssh to guts-environment and run below commands.

```
guts list
guts source-list
guts destination-list
```

Verify there are no current migrations and source & destinations.
We will add source and destinations.


Next we will add two sources, one openstack source and other vmware source through CLI.

### Add one VMware source

```
guts source-create vmware_source --driver guts.migration.drivers.sources.vsphere.VSphereSourceDriver --capabilities instance --registered_host guts-environment --credentials "{'host':'192.168.125.35','username':'administrator@vsphere.local','password':'test123','port':'443'}"
```

Verify that source is populated
``guts source-list`

Verify that resources populated
`guts resource-list`

### Let’s add a couple of destinations

We need to add two destinations to make sure better UI

```
guts destination-create openstack_destination --driver guts.migration.drivers.destinations.openstack.OpenStackDestinationDriver --capabilities instance,network,volume --registered_host guts-environment --credentials "{'auth_url':'http://192.168.100.26:5000/v2.0','username':'admin','password':'secret','tenant_name':'admin'}”
```

```
guts destination-create dummy_cloud --driver guts.migration.drivers.destinations.openstack.OpenStackDestinationDriver --capabilities instance,network,volume --registered_host guts-environment --credentials "{'auth_url':'http://192.168.100.27:5000/v2.0','username':'admin','password':'secret','tenant_name':'admin'}”
```

Verify that destination is populated

`guts destination-list`

### Let’s migrate

* Get resource id (Temp_MinimulUbuntu)
* Get destination id (OpenStack1)
* Get network name, flavor, secgroup

`guts create --name <MIGRATION_NAME> <RESOURCE-ID> <DESTINATION-ID> --extra_params “{‘flavor’:3’}”`

Example String: --extra_params="{'flavor':3,'secgroup':'default','network':'private','keypair':'win'}"
Creates migration process

`guts list`
To know the status of the migration, we will ssh to migrated VM and verify folder structure.
    
### Verify Migration

Run below command from destination machine

`ssh guts@<private_ip>`

And provide password : Openstack@1

Verify the state of machine.



## From UI

* Show services, resources & migrations page
* Make sure old migration is cleaned up and destination instance is done.
* Start a migration wizard
* Select one resource to migrate. Select an Instance to migrate.
* Click Next
* Select on destination and click your prefered, destination. Choose destination Openstack1
* Choose your network, keypair, security group, flavor etc.
* Give a dummy name
* Next
* Give a name and description to migration
* Ccick Migrate
* Keep refreshing page to verify.
