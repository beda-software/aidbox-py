# aidbox-py
Aidbox client for python.
This package provides an API for CRUD operations over Aidbox resources.

# Getting started
## Install
`pip install git+https://github.com/beda-software/aidbox-py.git`

## Async example
```Python
import asyncio
from aidboxpy import AsyncAidboxClient

async def main():
    # Create an instance
    client = AsyncAidboxClient(
        'http://localhost:8080',
        authorization='Bearer TOKEN'
    )

    # Search for patients
    resources = client.resources('Patient')  # Return lazy search set
    resources = resources.search(name='John').limit(10).page(2).sort('name')
    print(await resources.fetch())  # Returns list of AsyncAidboxResource

    # Create Organization resource
    organization = client.resource(
        'Organization',
        name='beda.software'
    )
    await organization.save()

    # Create new patient
    await client.resource(
        'Patient',
        id='new_patient'
    ).save()

    # Get patient resource by reference and delete
    patient_ref = client.reference('Patient', 'new_patient')
    patient_res = await patient_ref.to_resource()
    await patient_res.delete()

    # Iterate over search set
    org_resources = client.resources('Organization')
    async for org_resource in org_resources:
        print(org_resource.serialize())

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```

For additional examples see [fhir-py](https://github.com/beda-software/fhir-py/blob/master/README.md

# API
Import library:

`from aidboxpy import SyncAidboxClient`

or

`from aidboxpy import AsyncAidboxClient`

To create AidboxClient instance use:

`SyncAidboxClient(url, authorization='', schema=None, with_cache=False, extra_headers={})`

or

`AsyncAidboxClient(url, authorization='', schema=None, with_cache=False, extra_headers={})`

Returns an instance of the connection to the server which provides:
* .reference(resource_type, id, reference, **kwargs) - returns `SyncAidboxReference`/`AsyncAidboxReference` to the resource
* .resource(resource_type, **kwargs) - returns `SyncAidboxResource`/`AsyncAidboxResource` which described below
* .resources(resource_type) - returns `SyncAidboxSearchSet`/`AsyncAidboxSearchSet`

`SyncAidboxResource`/`AsyncAidboxResource`

provides:
* .serialize() - serializes resource
* .get_by_path(path, default=None) – gets the value at path of resource
* .save() - creates or updates resource instance
* .delete() - deletes resource instance
* .to_reference(**kwargs) - returns  `SyncAidboxReference`/`AsyncAidboxReference` for this resource

`SyncAidboxReference`/`AsyncAidboxReference`

provides:
* .to_resource(nocache=False) - returns `SyncAidboxResource`/`AsyncAidboxResource` for this reference

`SyncAidboxSearchSet`/`AsyncAidboxSearchSet`

provides:
* .search(param=value)
* .limit(count)
* .page(page)
* .sort(*args)
* .elements(*args, exclude=False)
* .include(resource_type, attr)
* .revinclude(resource_type, attr, recursive=False)
* .has(*args, **kwargs)
* `async` .fetch() - makes query to the server and returns a list of `Resource`
* `async` .fetch_all() - makes query to the server and returns a full list of `Resource`
* `async` .first() - returns `Resource` or None
* `async` .get(id=id) - returns `Resource` or raises `ResourceNotFound`
* `async` .count() - makes query to the server and returns the total number of resources that match the SearchSet