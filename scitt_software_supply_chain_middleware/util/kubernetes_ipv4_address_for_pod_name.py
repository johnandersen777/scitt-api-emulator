# Updated version: https://github.com/intel/Multi-llms-Chatbot-CloudNative-LangChain/blob/1bd6a844ebc57245f9fba8e7a87cde489cc4734d/2__LLMs_Proxy/server.py#L12-L34
import pathlib
from pprint import pprint

import yaml
import kubernetes
import kubernetes.client
from kubernetes.client.rest import ApiException
from kubernetes import client, config


def kubernetes_ipv4_address_for_pod_name(pod_name):
    # Load the service account kubeconfig
    configuration = kubernetes.client.Configuration()
    config.load_incluster_config(client_configuration=configuration)

    namespace = pathlib.Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read_text()

    with kubernetes.client.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = kubernetes.client.DiscoveryV1Api(api_client)

        api_response = api_instance.list_namespaced_endpoint_slice(namespace)

    found_endpoint = None
    for endpoint_slice in api_response.items:
        for endpoint in endpoint_slice.endpoints:
            if endpoint.target_ref.name == pod_name:
                found_endpoint = endpoint
                break
        if found_endpoint:
            break
    if not found_endpoint:
        raise Exception(f"Pod {pod_name} not found")

    # TODO Handle more cases than zeroith index?
    return found_endpoint.addresses[0]


print(kubernetes_ipv4_address_for_pod_name("backend-pod"))
