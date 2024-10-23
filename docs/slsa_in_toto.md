# SLSA (in-toto style)

Upstream for S2C2F sections: https://github.com/ossf/s2c2f/blob/98803e0a558e6d8cef4d2770864ffd3cf7618c65/specification/framework.md#appendix-relation-to-scitt

## S2C2F: Appendix: Relation to SCITT

> The [Supply Chain Integrity, Transparency, and Trust](https://github.com/ietf-scitt) initiative, or SCITT, is a set of proposed industry standards for managing the compliance of goods and services across end-to-end supply chains. In the future, we expect teams to output "attestations of conformance" to the S2C2F requirements and store it in SCITT. The format of such attestations is to be determined.

# S2C2F: Appendix: Mapping Secure Supply Chain Consumption Framework Requirements to Other Specifications

There are many other security frameworks, guides, and controls. This section maps the S2C2F Framework requirements to other relevant specifications including NIST SP 800-161, NIST SP 800-218, CIS Software Supply Chain Security Guide, OWASP Software Component Verification Standard, SLSA, and the CNCF Software Supply Chain Best Practices.

| **Requirement ID** | **Requirement Title** | **References** |
| --- | --- | --- |
| ING-1 | Use package managers trusted by your organization | **CIS SSC SG** : 3.1.5 <br /> **OWASP SCVS:** 1.2 <br /> **CNCF SSC:** Define and prioritize trusted package managers and repositories |
| ING-2 | Use an OSS binary repository manager solution | **OWASP SCVS:** 4.1 <br /> **CNCF SSC:** Define and prioritize trusted package managers and repositories |
| ING-3 | Have a Deny List capability to block known malicious OSS from being consumed | |
| ING-4 | Mirror a copy of all OSS source code to an internal location | **CNCF SSC:** Build libraries based upon source code |
| SCA-1 | Scan OSS for known vulnerabilities | **SP800218** : RV.1.1 <br /> **SP800161** : SA-10, SR-3, SR-4 <br /> **CIS SSC SG** : 1.5.5, 3.2.2 <br /> **OWASP SCVS:** 5.4 <br /> **CNCF SSC:** Verify third party artefacts and open source libraries, Scan software for vulnerabilities, Run software composition analysis on ingested software |
| SCA-2 | Scan OSS for licenses | **CIS SSC SG** : 1.5.6, 3.2.3 <br /> **OWASP SCVS:** 5.12 <br /> **CNCF SSC:** Scan software for license implications |
| SCA-3 | Scan OSS to determine if its end-of-life | **SP800218** : PW.4.1 <br /> **SP800161** : SA-4, SA-5, SA-8(3), SA-10(6), SR-3, SR-4 <br /> **OWASP SCVS:** 5.8 |
| SCA-4 | Scan OSS for malware | |
| SCA-5 | Perform proactive security review of OSS | **SP800218** : PW.4.4 <br /> **SP800161** : SA-4, SA-8, SA-9, SA-9(3), SR-3, SR-4, SR-4(3), SR-4(4) <br /> **OWASP SCVS:** 5.2, 5.3, |
| INV-1 | Maintain an automated inventory of all OSS used in development | **OWASP SCVS:** 1.1, 1.3, 1.8, 5.11 <br /> **CNCF SSC:** Track dependencies between open source components |
| INV-2 | Have an OSS Incident Response Plan | **SP800218** : RV.2.2 <br /> **SP800161** : SA-5, SA-8, SA-10, SA-11, SA-15(7) |
| UPD-1 | Update vulnerable OSS manually | |
| UPD-2 | Enable automated OSS updates | |
| UPD-3 | Display OSS vulnerabilities as comments in Pull Requests (PRs) | |
| AUD-1 | Verify the provenance of your OSS | **CIS SSC SG** : 3.2.4 <br /> **OWASP SCVS:** 1.10, 6.1 <br /> **SLSA v1.0:** Producing artifacts – Distribute provenance |
| AUD-2 | Audit that developers are consuming OSS through the approved ingestion method | **CIS SSC SG** : 4.3.3 |
| AUD-3 | Validate integrity of the OSS that you consume into your build | **CIS SSC SG** : 2.4.3 <br /> **OWASP SCVS:** 4.12 <br /> **CNCF SSC:** Verify third party artefacts and open source libraries |
| AUD-4 | Validate SBOMs of OSS that you consume into your build | **CNCF SSC:** Require SBOM from third party supplier |
| ENF-1 | Securely configure your package source files (i.e. nuget.config, .npmrc, pip.conf, pom.xml, etc.) | **SP800218** : PO.5.2 <br /> **CIS SSC SG** : 2.4.2, 3.1.7, 4.3.4, 4.4.2 |
| ENF-2 | Enforce usage of a curated OSS feed that enhances the trust of your OSS | **SP800218** : PO.5.2 <br /> **CIS SSC SG** : 2.4.3, 3.1.1, 3.1.3 |
| REB-1 | Rebuild the OSS in a trusted build environment, or validate that it is reproducibly built | **CIS SSC SG** : 2.4.4 |
| REB-2 | Digitally sign the OSS you rebuild | **SP800218** : PS.2.1 |
| REB-3 | Generate SBOMs for OSS that you rebuild | **SP800218** : PS.3.2 <br /> **SP800161** : SA-8, SR-3, SR-4 <br /> **CIS SSC SG** : 2.4.5 <br /> **OWASP SCVS:** 1.4, 1.7 <br /> **CNCF SSC:** Generate an immutable SBOM of the code |
| REB-4 | Digitally sign the SBOMs you produce | **CIS SSC SG** : 2.4.6 |
| FIX-1 | Implement a change in the code to address a zero-day vulnerability, rebuild, deploy to your organization, and confidentially contribute the fix to the upstream maintainer | |

## Webhook endpoint

Targets are new commits, branches, tags, and their CI/CD (status check) results

- Transforms GitHub webhook payloads into statements
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/v1/statement.md
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/predicates/test-result.md
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/predicates/cyclonedx.md
- https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#download-a-repository-archive-tar

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "<NAME>",
      "digest": {"<ALGORITHM>": "<HEX_VALUE>"}
    },
    ...
  ],
  "predicateType": "https://in-toto.io/attestation/test-result/v0.1",
  "predicate": {
      "result": "PASSED|WARNED|FAILED",
      "configuration": ["<ResourceDescriptor>", ...],
      "url": "<URL>",
      "passedTests": ["<TEST_NAME>", ...],
      "warnedTests": ["<TEST_NAME>", ...],
      "failedTests": ["<TEST_NAME>", ...]
  }
}
```

- https://github.com/pdxjohnny/scitt-api-emulator/blob/demo-instance/docs/sbom_and_vex.md

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "<NAME>",
      "digest": {"<ALGORITHM>": "<HEX_VALUE>"}
    },
    ...
  ],
  "predicateType": "https://spdx.dev/Document/v2.3",
  "predicate": {
    "SPDXID" : "SPDXRef-DOCUMENT",
    "spdxVersion" : "SPDX-2.3",
    ...
  }
}
```
