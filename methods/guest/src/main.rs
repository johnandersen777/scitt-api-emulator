/*
 * Need for OIDC relay validation:
 * - During rust compile
 *   - JSON Web Keys
 *   - Issuer URIs
 *   - Audiance
 * - Inputs
 *   - Token
 *
CONTRIBUTING.md:        - She auths to job in TEE (SGX in this example) local SCITT via OIDC, the SCITT notary and ledger are unified in this example and a claim is inserted that she had a valid OIDC token for job_workflow_sha + repositoryUri + repository_id + job.. The enclave is then dumped at the end of the job so that it can be joined to an other transparency services. This enables decentralized hermetic builds via federation of transparency services (by grafting them into org sepcific registires ad-hoc via CD eventing of forge federation).
CONTRIBUTING.md:    - The notary is what's verifying the OIDC token.
CONTRIBUTING.md:Virtual branch - shared context dependent trains of thought within a poly-repo environment. If the overlays of an entity currently federating with. The N+1 federation new data event is always determined by a KERI duplicity detection protected channel (this is critical because or else we are not able to see who is being duplictus over time, which we need for the relying parties analysis of ClearForTakeoff for AI agent (workload) identity (OIDC, sould based auth). The tcb for trust evaluation is also party of relying party inputs.
docs/arch/alice/discussion/0023/reply_0050.md:  - UCAN seems like a good way to do OIDC in the near future. From what we can tell this could be very useful in embedded applications. We're hoping we can leverage UCAN/Verifiable Credentials to get TPM/SGX/TDX attestations from hardware to incorporate into provenance/attestation information. DIDs and UCAN are the primitives we can use for data and auth in web3. All devices can speak VC, we can do that similar to Peer DID/DIDCommv2. It's just PGP on JSON blobs. Engaging with the https://ucan.xyz community to identify web2/web3 gateways of interest from an auth perspective (ODIC GitHub Actions Token -> UCAN token? Peer DID referencing the ODIC token?) Hoping we can ensure their auth format will support attestations from DICE devices. Then we can have our firmware through WASM all talking the same auth which will make things much easier as Alice moves through the devices.
docs/arch/alice/discussion/0032/reply_0001.md:  - SPIFFE workload identify (similar to the github workflow OIDC claim stuff)
docs/arch/alice/discussion/0036/reply_0068.md:  - [ ] GitHub Action Ci job to on trigger to document how to make this happen on same repo (since token write permissions will only existing for OIDC token of job within repo, could use different token to support against other repos)
docs/discussions/alice_engineering_comms/0042/reply_0000.md:> You can then use curl to retrieve a JWT from the GitHub OIDC provider. For example:
docs/discussions/alice_engineering_comms/0042/reply_0000.md:      > Sigstore relies on the widely used OpenID Connect (OIDC) protocol to prove identity. When running something like cosign sign, users will complete an OIDC flow and authenticate via an identity provider (GitHub, Google, etc.) to prove they are the owner of their account. Similarly, automated systems (like GitHub Actions) can use Workload Identity or [SPIFFE](https://spiffe.io/) Verifiable Identity Documents (SVIDs) to authenticate themselves via OIDC. The identity and issuer associated with the OIDC token is embedded in the short-lived certificate issued by Sigstore’s Certificate Authority, Fulcio.
docs/discussions/alice_engineering_comms/0054/reply_0000.md:- sigstore github actions OIDC token
docs/discussions/alice_engineering_comms/0055/reply_0000.md:    > GITSIGN_OIDC_CLIENT_ID | ✅ | sigstore | OIDC client ID for application
docs/discussions/alice_engineering_comms/0055/reply_0000.md:    > GITSIGN_OIDC_ISSUER | ✅ | https://oauth2.sigstore.dev/auth | OIDC provider to be used to issue ID token
docs/discussions/alice_engineering_comms/0055/reply_0000.md:    > GITSIGN_OIDC_REDIRECT_URL | ✅ |   | OIDC Redirect URL
docs/discussions/alice_engineering_comms/0056/index.md:       - We will attest data using reusable workflows, OIDC, and sigstore
docs/discussions/alice_engineering_comms/0058/reply_0000.md:    - Send back secrets and OIDC token to callback endpoint using public key provided as input (TODO KERI)
docs/discussions/alice_engineering_comms/0062/reply_0000.md:  - How would tie in with OIDC GitHub Actions / sigstore work?
docs/discussions/alice_engineering_comms/0065/reply_0001.md:  - https://satori-syntax-highlighter.vercel.app/api/highlighter?fontSize=4&lang=python&background=%23E36FB7&code=%22%22%22%0AUsage%0A%2A%2A%2A%2A%2A%0A%0A%2A%2ATODO%2A%2A%0A%0A-%20Packaging%0A%0A..%20code-block%3A%3A%20console%0A%0A%20%20%20%20%24%20echo%20Package%20python%20into%20wheel%20given%20entry%20points%20to%20overlay%20dffml.overlays.alice.please.contribute.recommended_community_standards%0A%20%20%20%20%24%20echo%20Embed%20JWK%0A%20%20%20%20%24%20echo%20JWK%20fulcio%20OIDC%3F%0A%20%20%20%20%24%20echo%20upload%20to%20twitter%20or%20somewhere%0A%20%20%20%20%24%20echo%20download%20and%20verify%20using%20JWK%2C%20show%20OIDC%20for%20online%20lookup%0A%20%20%20%20%24%20pip%20install%20package.zip%0A%20%20%20%20%24%20alice%20shouldi%20contribute%20-log%20debug%20-keys%20https%3A%2F%2Fexamples.com%2Frepowith%2Fmyconfigjson%0A%0A%22%22%22%0Aimport%20json%0Aimport%20pathlib%0Afrom%20typing%20import%20NewType%0A%0AMyConfig%20%3D%20NewType%28%22MyConfig%22%2C%20object%29%0AMyConfigUnvalidated%20%3D%20NewType%28%22MyConfigUnvalidated%22%2C%20object%29%0AMyConfigProjectName%20%3D%20NewType%28%22MyConfigProjectName%22%2C%20str%29%0AMyConfigDirectory%20%3D%20NewType%28%22MyConfigDirectory%22%2C%20str%29%0A%0A%0Adef%20read_my_config_from_directory_if_exists%28%0A%20%20%20%20directory%3A%20MyConfigDirectory%2C%0A%29%20-%3E%20MyConfigUnvalidated%3A%0A%20%20%20%20%22%22%22%0A%20%20%20%20%3E%3E%3E%20import%20json%0A%20%20%20%20%3E%3E%3E%20import%20pathlib%0A%20%20%20%20%3E%3E%3E%20import%20tempfile%0A%20%20%20%20%3E%3E%3E%0A%20%20%20%20%3E%3E%3E%20with%20tempfile.TemporaryDirectory%28%29%20as%20tempdir%3A%0A%20%20%20%20...%20%20%20%20%20_%20%3D%20pathlib.Path%28tempdir%2C%20%22.myconfig.json%22%29.write_text%28json.dumps%28%7B%22name%22%3A%20%22Hello%20World%22%7D%29%29%0A%20%20%20%20...%20%20%20%20%20print%28read_my_config_from_directory_if_exists%28tempdir%29%29%0A%20%20%20%20%7B%27name%27%3A%20%27Hello%20World%27%7D%0A%20%20%20%20%22%22%22%0A%20%20%20%20path%20%3D%20pathlib.Path%28directory%2C%20%22.myconfig.json%22%29%0A%20%20%20%20if%20not%20path.exists%28%29%3A%0A%20%20%20%20%20%20%20%20return%0A%20%20%20%20return%20json.loads%28path.read_text%28%29%29%0A%0A%0Adef%20validate_my_config%28%0A%20%20%20%20config%3A%20MyConfigUnvalidated%2C%0A%29%20-%3E%20MyConfig%3A%0A%20%20%20%20%23%20TODO%28security%29%20json%20schema%20valiation%20of%20myconfig%20%28or%0A%20%20%20%20%23%20make%20done%20automatically%20by%20operation%20manifest%20schema%0A%20%20%20%20%23%20validation%20on%20InputNetwork%2C%20maybe%2C%20just%20one%20option%2C%0A%20%20%20%20%23%20or%20maybe%20similar%20to%20how%20prioritizer%20gets%20applied%2C%0A%20%20%20%20%23%20or%20maybe%20this%20is%20an%20issue%20we%20already%20track%3A%20%231400%29%0A%20%20%20%20return%20config%0A%0A%0Adef%20my_config_project_name%28%0A%20%20%20%20config%3A%20MyConfig%2C%0A%29%20-%3E%20MyConfigProjectName%3A%0A%20%20%20%20%22%22%22%0A%20%20%20%20%3E%3E%3E%20print%28my_config_project_name%28%7B%22name%22%3A%20%22Hello%20World%22%7D%29%29%0A%20%20%20%20Hello%20World%0A%20%20%20%20%22%22%22%0A%20%20%20%20return%20config%5B%22name%22%5D%0A
docs/discussions/alice_engineering_comms/0065/reply_0001.md:    $ echo JWK fulcio OIDC?
docs/discussions/alice_engineering_comms/0065/reply_0001.md:    $ echo download and verify using JWK, show OIDC for online lookup
docs/discussions/alice_engineering_comms/0074/reply_0000.md:  - [ ] Demo metric scan with SCITT receipt used to auth upload results to HTTP server (stream of consciousness / webhook server). Root trust in OIDC token similar to fulcio/sigstore github actions slsa demo.
docs/discussions/alice_engineering_comms/0080/reply_0000.md:    - Demo metric scan with SCITT receipt used to auth upload results to HTTP server (stream of consciousness / webhook server). Root trust in OIDC token similar to fulcio/sigstore github actions slsa demo.
docs/discussions/alice_engineering_comms/0083/reply_0000.md:    - > // NOTE: VP, OIDC, DIDComm, or CHAPI outer wrapper properties would be at outer layer
docs/discussions/alice_engineering_comms/0086/reply_0000.md:    - Require SCITT recit with manifest of artifact sha and OIDC token
docs/discussions/alice_engineering_comms/0086/reply_0001.md:              - Registration policy controls what signed statemtnst can be made transparent, it can alos say who can put signed statemtenst in (OIDC) and make them transparent via this instance
docs/discussions/alice_engineering_comms/0086/reply_0001.md:          - Play with OIDC and SCITT
docs/discussions/alice_engineering_comms/0089/reply_0000.md:- OIDC
docs/discussions/alice_engineering_comms/0090/reply_0000.md:  - Also touched on recent OIDC verification via notary
docs/discussions/alice_engineering_comms/0102/reply_0000.md:      - [ ] Authenticated push via OIDC -> Notary -> SCITT Receipt patterns
docs/discussions/alice_engineering_comms/0123/reply_0000.md:  - [ ] OIDC to OIDCVC proxy setup
docs/discussions/alice_engineering_comms/0123/reply_0000.md:  - [ ] DevCloud OIDC proxy for auto auth
docs/discussions/alice_engineering_comms/0147/reply_0000.md:  - > Orie Steele: My favorite part of the DID Spec is that it invites you to project existing crypto or public key spaces into its identifier format for the purpose of graph analysis. This projects explores projecting JWK, JWT, JWS, JWE and OIDC representations into a DID space.
docs/discussions/alice_engineering_comms/0152/reply_0000.md:- Harbor has webhooks and OIDC auth support
docs/discussions/alice_engineering_comms/0152/reply_0000.md:  - > OIDC support: Harbor leverages OpenID Connect (OIDC) to verify the identity of users authenticated by an external authorization server or identity provider. Single sign-on can be enabled to log into the Harbor portal.
docs/discussions/alice_engineering_comms/0155/reply_0000.md:    > I'm raising this as a potential enhancement/addition to current set of X.509 extensions used by Sigstore when encapsulating GitHub Actions OIDC claims, based on [this comment](https://internals.rust-lang.org/t/pre-rfc-using-sigstore-for-signing-and-verifying-crates/18115/14?u=woodruffw) in the pre-RFC discussion for Sigstore's integration into `cargo`/`crates.io`.
docs/discussions/alice_engineering_comms/0155/reply_0000.md:> At the moment, there are two primary OIDC claims from GitHub Actions-issued tokens that get embedded in Fulcio-issued certificates as X.509v3 extensions:
docs/discussions/alice_engineering_comms/0155/reply_0000.md:> 1. The SAN itself, which contains the value of `job_workflow_ref` from the OIDC token
docs/discussions/alice_engineering_comms/0155/reply_0000.md:> 2. `1.3.6.1.4.1.57264.1.5`, which contains the value of the `repository` claim from the OIDC token (in `org/repo` "slug" form)
docs/discussions/alice_engineering_comms/0156/reply_0000.md:      - Ray: If I want to audit to say that Ray was Ray, I have to walk back to the OIDC to find out that Ray was Ray.
docs/discussions/alice_engineering_comms/0156/reply_0000.md:      - Zach: The OIDC tokens aren't safe to publish. We do have a severed link there, dpop looking at that
docs/discussions/alice_engineering_comms/0161/reply_0000.md:- Actor discovery via notery recipt for OIDC for workflow (see recent linked spdx issue)
docs/discussions/alice_engineering_comms/0173/reply_0000.md:        - [ ] ASAP OIDC auth
docs/discussions/alice_engineering_comms/0177/reply_0001.md:  - John (not said): These identities could also be ephemeral roles whcih are tied to attested compute (aka built from CI/CD and deployed to confidential compute, example: build_images_containers.yml -> #1247 -> Project Amber -> OIDC -> more builds -> SCITT)
docs/discussions/alice_engineering_comms/0217/reply_0000.md:  - Okay DEX helps us bridge OAuth to OIDC, I forgot, it's been a while
docs/discussions/alice_engineering_comms/0220/reply_0000.md:routers/web/web.go-             m.Get("/openid-configuration", auth.OIDCWellKnown)
docs/discussions/alice_engineering_comms/0222/reply_0000.md:CHANGELOG.md:  * Add well-known config for OIDC (#15355)
docs/discussions/alice_engineering_comms/0224/reply_0000.md:  - [ ] SCITT instance whos policy makes it act as the OIDC notary proxy. A service that sits in front of an instance which issues claims based on valid OIDC and job_workflow_ref. The instance it submits claims to has the did:web or did:pwq or did:keri in its allowlist. The content address or content of the  receipt is submitted within the claim whose receipt is attached to the releaseasset.json as a property base32 encoded. Upon federation of the releaseasset receipt the receiver now knows upload auth checked out. Insert policy on federation event you create two receipts, first triahing incoming into cobtext localvthen reciot for inclustyoon in context local. thjis way we can traberse back but maintain payload
docs/discussions/alice_engineering_comms/0225/reply_0000.md:- Related issues to insert policy by `job_workflow_sha` + `repositoryUri` + `repository_id` OIDC SCITT notary
docs/discussions/alice_engineering_comms/0227/reply_0000.md:        - She auths to SCITT via OIDC, she proves she had a valid token because she's issued a receipt. The whole process is wrapped up inside an enclave which runs within a parallel job. The enclave is then dumped at the end of the job so that it can be joined to an other transparency services. This enables decentralized hermetic builds.
docs/discussions/alice_engineering_comms/0227/reply_0000.md:    - The notary is what's verifying the OIDC token.
docs/discussions/alice_engineering_comms/0230/reply_0000.md:  - OIDC publish to PyPi style registry, we'll try using this for 2nd party local registry
docs/discussions/alice_engineering_comms/0387/reply_0000.md:      - [x] OIDC plugin - https://github.com/scitt-community/scitt-api-emulator/pull/31
docs/discussions/alice_engineering_comms/0405/reply_0000.md:  - `job_workflow_ref` is susceptible to RepoJacking/renaming attacks. Could we please get `job_workflow_repository_id` and `job_workflow_repository_owner_id` added to OIDC token claims for reusable workflows?
docs/discussions/alice_engineering_comms/0421/reply_0000.md:  - This also uses Moo auth, ideally we use something more standard like OIDC to not rock the boat too much.
docs/discussions/alice_engineering_comms/0421/reply_0000.md:  - We'll leverage the work we did on OIDC for plugin helper infra and instantiation of the federation class.
docs/discussions/alice_engineering_comms/0421/reply_0000.md:  - [ ] Could we issue OIDC tokens off the mechanical bull manged keys?
docs/discussions/alice_engineering_comms/0421/reply_0000.md:    - It looks like `bovine.clients.bearer` is used to talk to Mastodon's API. If we wanted to make Bovine accept token auth from a client signed OIDC token we could add routes to the Herd server for the jwks
docs/discussions/alice_engineering_comms/0424/reply_0000.md:- Pre OIDC rebased into federation branch from main: https://github.com/scitt-community/scitt-api-emulator/commit/ac0d45e65468309c40ad1cbfae24bd7c8ab0b448
docs/discussions/alice_engineering_comms/0432/reply_0000.md:echo 'OIDC interop ^ ?'
docs/discussions/alice_engineering_comms/0441/reply_0001.md:- OIDC issuer as issuer of notary
docs/discussions/alice_engineering_comms/0441/reply_0001.md:- Discussion with Steve around OIDC issuer
docs/discussions/alice_engineering_comms/0443/reply_0000.md:      - **TODO(@pdxjohnny)** update OIDC thread with flushed out example and registration policy doc with jsonschema + CWT / JWT verification of issuer
docs/discussions/alice_engineering_comms/0443/reply_0000.md:    - Furthered work on API access control (OIDC)
docs/discussions/alice_engineering_comms/0444/reply_0001.md:# Example with OIDC Auth
docs/discussions/alice_engineering_comms/0444/reply_0001.md:# OIDC_TOKEN=$(curl -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=https://scitt.example.org")
docs/discussions/alice_engineering_comms/0444/reply_0001.md:# scitt-emulator client submit-claim --claim claim.cose --out claim.receipt.cbor --url https://scitt.example.org --cacert "${REQUESTS_CA_BUNDLE}" --token "${OIDC_TOKEN}"
docs/discussions/alice_engineering_comms/0449/reply_0000.md:      - [ ] Example: We have a content addressable resource protected via OIDC auth. We can embed the address of the resource into the payload along with an OIDC token whose audience (or other claims, but with GitHub Actions not natively possible to customize, could use a separte reusable workflow to issue to, but would need to leave open until data is accessed to avoid token revokation on reusable completion), parameter ideally includes that this token will be used to access the resource which was uploaded prior to the payload of the statement being handed to the notary.
docs/discussions/alice_engineering_comms/0450/reply_0000.md:  - [ ] SCITT ActivityPub Actor registration could be allowlisted based on OIDC protected endpoint
docs/discussions/alice_engineering_comms/0558/reply_0000.md:      # Grab an OIDC token too.
docs/discussions/alice_engineering_comms/0558/reply_0000.md:      OIDC_TOKEN=$(curl -s $ISSUER_URL)
docs/discussions/alice_engineering_comms/0558/reply_0000.md:      echo "OIDC_TOKEN=$OIDC_TOKEN" >> $GITHUB_ENV
docs/discussions/alice_engineering_comms/0561/reply_0000.md:    - kcp/k8s OIDC token issuance leveraging that RBAC
docs/discussions/alice_engineering_comms/0573/reply_0000.md:  - [x] SCITT OIDC MUST be combined with policy engine `subject`. OIDC tokens should be issued of receipt chains
docs/discussions/alice_engineering_comms/0575/reply_0000.md:  - This is the perfect place for our OIDC phase 1 relying party to go
docs/discussions/alice_engineering_comms/0649/reply_0000.md:  - There's not API for adding applications which use forgejo for OIDC based auth
docs/discussions/alice_engineering_comms/0649/reply_0000.md:- OIDC confidential client flow
docs/discussions/alice_engineering_comms/0649/reply_0000.md:  - [x] Deploy Directus where auth is from ForgeJo via OIDC
docs/discussions/alice_engineering_comms/0660/reply_0000.md:- Guac as firewall, directus as insert and update graphql into guac db from workflow id’d agents or worflows. Also setup registry for each forge. OIDC all to forgejo. DO scripting from infra branch
docs/tutorials/rolling_alice/0000_architecting_alice/0005_stream_of_consciousness.md:       - We will attest data using reusable workflows, OIDC, and sigstore
docs/tutorials/rolling_alice/0000_architecting_alice/0006_os_decentralice.md:- sigstore github actions OIDC token
*/
use risc0_zkvm::guest::env;

fn main() {
    // TODO: Implement your guest code here

    // read the input
    let input: u32 = env::read();

    // TODO: do something with the input

    // write public output to the journal
    env::commit(&input);
}
