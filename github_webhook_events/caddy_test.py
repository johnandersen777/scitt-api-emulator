import http

import snoop
import httpx


class CaddyConfigLoadError(Exception):
    pass


async def main():
    slug = "files"

    transport = httpx.AsyncHTTPTransport(uds="/tmp/mcp-reverse-proxy.sock")
    async with httpx.AsyncClient(transport=transport) as client:
        response = await client.get(
            "http://127.0.0.1/caddy-admin/config/",
        )
        caddy_config = response.json()
        snoop.pp(response.status_code, response.headers, caddy_config)
        exists = False
        proxy_route_caddy_admin = None
        for route in caddy_config['apps']['http']['servers']['srv0']['routes']:
            for handle in route['handle']:
                for proxy_route in handle['routes']:
                    for match in proxy_route['match']:
                        for path in match['path']:
                            if path == '/caddy-admin/*':
                                proxy_route_caddy_admin = proxy_route
                            if path == f'/{slug}/*':
                                exists = True
        if exists:
            return
        proxy_route_new = json.loads(
            json.dumps(
                proxy_route_caddy_admin,
            ).replace("caddy-admin", slug),
        )
        added = False
        for route in caddy_config['apps']['http']['servers']['srv0']['routes']:
            for handle in route['handle']:
                for proxy_route in handle['routes']:
                    for match in proxy_route['match']:
                        for path in match['path']:
                            if path == '/caddy-admin/*':
                                added = True
                                handle['routes'].append(proxy_route_new)
                    if added:
                        break
        response = await client.post(
            "http://127.0.0.1/caddy-admin/load",
            headers={"Content-Type": "application/json"},
            content=json.dumps(caddy_config),
        )
        if response.status_code != http.HTTPStatus.OK.value:
            raise CaddyConfigLoadError(f"{response.status_code}: {response.text}")


if __name__ == "__main__":
    asyncio.run(main())
