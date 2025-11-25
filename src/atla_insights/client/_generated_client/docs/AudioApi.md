# _generated_client.AudioApi

All URIs are relative to *https://app.atla-ai.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_audio_by_id**](AudioApi.md#get_audio_by_id) | **GET** /api/sdk/v1/audio/{audioId} | Get a single audio file by ID


# **get_audio_by_id**
> bytearray get_audio_by_id(audio_id)

Get a single audio file by ID

Streams the audio file bytes for the given audio ID.

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
    api_instance = _generated_client.AudioApi(api_client)
    audio_id = 'audio_id_example' # str |

    try:
        # Get a single audio file by ID
        api_response = api_instance.get_audio_by_id(audio_id)
        print("The response of AudioApi->get_audio_by_id:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AudioApi->get_audio_by_id: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **audio_id** | **str**|  |

### Return type

**bytearray**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: audio/mpeg

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successfully retrieved audio file |  -  |
**401** | Unauthorized - Invalid or missing API key |  -  |
**404** | Audio file not found or access denied |  -  |
**500** | Internal Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
