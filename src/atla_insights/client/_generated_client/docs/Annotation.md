# Annotation


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**span_id** | **str** |  | 
**failure_mode** | **str** |  | 
**atla_critique** | **str** |  | 
**id** | **str** |  | 

## Example

```python
from _generated_client.models.annotation import Annotation

# TODO update the JSON string below
json = "{}"
# create an instance of Annotation from a JSON string
annotation_instance = Annotation.from_json(json)
# print the JSON string representation of the object
print(Annotation.to_json())

# convert the object into a dict
annotation_dict = annotation_instance.to_dict()
# create an instance of Annotation from a dict
annotation_from_dict = Annotation.from_dict(annotation_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


