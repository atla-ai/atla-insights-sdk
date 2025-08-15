# CustomMetricValue


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**trace_id** | **str** |  | 
**custom_metric_id** | **str** |  | 
**value** | **str** |  | 
**custom_metric** | [**CustomMetric**](CustomMetric.md) |  | [optional] 

## Example

```python
from _generated_client.models.custom_metric_value import CustomMetricValue

# TODO update the JSON string below
json = "{}"
# create an instance of CustomMetricValue from a JSON string
custom_metric_value_instance = CustomMetricValue.from_json(json)
# print the JSON string representation of the object
print(CustomMetricValue.to_json())

# convert the object into a dict
custom_metric_value_dict = custom_metric_value_instance.to_dict()
# create an instance of CustomMetricValue from a dict
custom_metric_value_from_dict = CustomMetricValue.from_dict(custom_metric_value_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


