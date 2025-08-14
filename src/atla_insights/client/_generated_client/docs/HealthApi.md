# _generated_client.HealthApi

All URIs are relative to *https://app.atla-ai.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_api_health**](HealthApi.md#get_api_health) | **GET** /api/health | Health check


# **get_api_health**
> get_api_health()

Health check

Returns 200 if the server is healthy

### Example


```python
import _generated_client
from _generated_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://app.atla-ai.com
# See configuration.py for a list of all supported configuration parameters.
configuration = _generated_client.Configuration(
    host = "https://app.atla-ai.com"
)


# Enter a context with an instance of the API client
with _generated_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = _generated_client.HealthApi(api_client)

    try:
        # Health check
        api_instance.get_api_health()
    except Exception as e:
        print("Exception when calling HealthApi->get_api_health: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

