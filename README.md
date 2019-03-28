# aidbox-py
Aidbox client for python.
This package provides an API for CRUD operations over Aidbox resources

# API
Import library:

`from aidboxpy import AidboxClient`

To create AidboxClient instance use:

`AidboxClient(url, authorization='', schema=None, with_cache=False)`

Returns an instance of the connection to the server which provides:
* .reference(resource_type, id, reference, **kwargs) - returns `AidboxReference` to the resource
* .resource(resource_type, **kwargs) - returns `AidboxResource` which described below
* .resources(resource_type) - returns `AidboxSearchSet`

`AidboxResource`

provides:
* .save() - creates or updates resource instance
* .delete() - deletes resource instance
* .to_reference(**kwargs) - returns  `AidboxReference` for this resource

`AidboxReference`

provides:
* .to_resource(nocache=False) - returns `AidboxResource` for this reference

`AidboxSearchSet`

provides:
* .search(param=value)
* .limit(count)
* .page(page)
* .sort(*args)
* .elements(*args, exclude=False)
* .include(resource_type, attr)
* .fetch() - makes query to the server and returns a list of `AidboxResource`
* .fetch_all() - makes query to the server and returns a full list of `AidboxResource`
* .first() - returns `AidboxResource` or None
* .get(id=id) - returns `AidboxResource` or raises `ResourceNotFound`

# Usage

Create an instance
```python
client = AidboxClient(url='http://path-to-aidbox-server', authorization='Bearer TOKEN')
```

Fetch list of resource's instances
```python
resources = client.resources('Patient')  # Return lazy search set
resources = resources.search(name='John').limit(10).page(2).sort('name')

resources.fetch()  # Returns list of FHIRResource
```

Get the particular instance of resource
```python
res = client.resources('Patient').get(id='ID')
```
