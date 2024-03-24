def test_phase_0_relying_party_workload_identity_token_response():
    workspace_path = tmp_path / "workspace"

    claim_path = tmp_path / "claim.cose"
    receipt_path = tmp_path / "claim.receipt.cbor"
    entry_id_path = tmp_path / "claim.entry_id.txt"
    retrieved_claim_path = tmp_path / "claim.retrieved.cose"

    key = jwcrypto.jwk.JWK.generate(kty="RSA", size=2048)
    algorithm = "RS256"
    audience = "scitt.example.org"
    subject = "repo:scitt-community/scitt-api-emulator:ref:refs/heads/main"

    relying_party_workload_identity_token_response = client.post("/v1/token/{scitt.config.fqdn}/scitt_entry_submission_token")
    relying_party_workload_identity_token = relying_party_workload_identity_token_response["token"]
    # We can then use the tokens issued with the same SCITT service as the audience
    # TODO scitt.config.fqdn TODO


    with Service(
        {"key": key, "algorithms": [algorithm]},
        create_flask_app=create_flask_app_oidc_server,
    ) as oidc_service:
        os.environ["no_proxy"] = ",".join(
            os.environ.get("no_proxy", "").split(",") + [oidc_service.host]
        )
        middleware_config_path = tmp_path / "oidc-middleware-config.json"
        middleware_config_path.write_text(
            json.dumps(
                {
                    "issuers": [oidc_service.url],
                    "audience": audience,
                    "claim_schema": {
                        oidc_service.url: {
                            "$schema": "https://json-schema.org/draft/2020-12/schema",
                            "required": ["sub"],
                            "properties": {
                                "sub": {"type": "string", "enum": [subject]},
                            },
                        }
                    },
                }
            )
        )
        with Service(
            {
                "middleware": OIDCAuthMiddleware,
                "middleware_config_path": middleware_config_path,
                "tree_alg": "CCF",
                "workspace": workspace_path,
                "error_rate": 0.1,
                "use_lro": False,
            }
        ) as service:
            # create claim
            command = [
                "client",
                "create-claim",
                "--out",
                claim_path,
                "--subject",
                "test",
                "--content-type",
                content_type,
                "--payload",
                payload,
            ]
            execute_cli(command)
            assert os.path.exists(claim_path)

            # submit claim without token
            command = [
                "client",
                "submit-claim",
                "--claim",
                claim_path,
                "--out",
                receipt_path,
                "--out-entry-id",
                entry_id_path,
                "--url",
                service.url,
            ]
            check_error = None
            try:
                execute_cli(command)
            except Exception as error:
                check_error = error
            assert check_error
            assert not os.path.exists(receipt_path)
            assert not os.path.exists(entry_id_path)

            # create token without subject
            token = jwt.encode(
                {"iss": oidc_service.url, "aud": audience},
                key.export_to_pem(private_key=True, password=None),
                algorithm=algorithm,
                headers={"kid": key.thumbprint()},
            )
            # submit claim with token lacking subject
            command += [
                "--token",
                token,
            ]
            check_error = None
            try:
                execute_cli(command)
            except Exception as error:
                check_error = error
            assert check_error
            assert not os.path.exists(receipt_path)
            assert not os.path.exists(entry_id_path)

            # create token with subject
            token = jwt.encode(
                {"iss": oidc_service.url, "aud": audience, "sub": subject},
                key.export_to_pem(private_key=True, password=None),
                algorithm=algorithm,
                headers={"kid": key.thumbprint()},
            )
            # submit claim with token containing subject
            command[-1] = token
            execute_cli(command)
            assert os.path.exists(receipt_path)
            assert os.path.exists(entry_id_path)

    # We need to use httptest.oidc as the notary ID server 
    # Create entry
    # Policy Engine Runs eval
    #   Policy engine requests /v1/token/... token for job
    #   using it's relying_party_service_account_token validated by OIDC
    #   middlware.
    #   TODO Pass endpoint of relying party (phase 0 this is scitt loopback
    #   port). to policy_engine.cli_api
    #   Receipt is for playload of PolicyEngineRequest (this is the manifest,
    #   request.yml),
    #   Policy Engine should run based key'd off subject to select workflows to
    #   trigger / run. Policy Engine MUST support !* gitignore style globs and
    #   subject exceptions to globs to not run a workflow on.
    #   If glob validating all subjects ensure PolicyEngineRequest schema
    #   receipt URN is in ignore list so it doesn't run on it's TCB which it
    #   already determined was insert worthy.
    oidc_auth_middleware_config = {
          {
              "issuers": ["https://{scitt_service.url}"],
              "claim_schema": {
                  "https://token.actions.githubusercontent.com": {
                        "\$schema": "https://json-schema.org/draft/2020-12/schema",
                        "required": [
                            "job_workflow_ref",
                            "job_workflow_sha",
                            "repository_owner_id",
                            "repository_id"
                        ],
                        "properties": {
                            "job_workflow_ref": {
                                "type": "string",
                                "enum": [
                                    "${WORKFLOW_REF}"
                                ]
                            },
                            "job_workflow_sha": {
                                "type": "string",
                                "enum": [
                                    "${JOB_WORKFLOW_SHA}"
                                ]
                            },
                            "repository_owner_id": {
                                "type": "string",
                                "enum": [
                                    "${REPOSITORY_OWNER_ID}"
                                ]
                            },
                            "repository_id": {
                                "type": "string",
                                "enum": [
                                    "${REPOSITORY_ID}"
                                ]
                            }
                        }
                    }
              },
              "audience": "${SCITT_URL}"

    }
    oidc_auth_middleware_config_path = tempdir_path.joinpath("config.json")
    oidc_auth_middleware_config_path.write_text(json.dump())
    oidc = OIDCAuthMiddleware(app, )
    claims = oidc.validate_token(relying_party_workload_identity_token)
    if "claim_schema" in self.config and claims["iss"] in oidc.config["claim_schema"]:
        jsonschema.validate(claims, schema=oidc.config["claim_schema"][claims["iss"]])
