# Normalized Comss hosts

An automatically updated HOSTS file with **exactly one IP hostname pair per line**, preserving multiple IPs for a domain and removing exact duplicate pairs.

**Raw link:** https://raw.githubusercontent.com/defffis/host/main/comss/hosts

**Default source:** https://raw.githubusercontent.com/Noktomezo/RussiaFancyLists/main/lists/hosts/comss.hosts

## Configure the source URL

Open **Repository Settings → Secrets and variables → Actions → Variables → New repository variable** and create `SOURCE_URL`. Set its value to the HTTPS URL of any compatible HOSTS source. If not defined, the workflow uses the default Comss source above.

The workflow runs approximately every 3 hours (GitHub schedule is best-effort), on manual start via **Actions → Update normalized hosts → Run workflow**, and when parser or workflow files change.

### Example

Input:

    103.137.248.145 anthropic.com api.anthropic.com
    ::1 localhost ip6-localhost

Output:

    103.137.248.145 anthropic.com
    103.137.248.145 api.anthropic.com
    ::1 localhost
    ::1 ip6-localhost

Comments and malformed entries are dropped. Input must be valid UTF-8, reachable through HTTPS, and 20 MiB or smaller. Exact repeated IP/hostname pairs are removed. Existing output remains unchanged if the download fails or contains zero valid records.

**Security note:** HOSTS entries override DNS resolution for the specified hostnames. Use only a trusted upstream source. This repository republishes upstream addresses and does not verify that destination IPs belong to their respective services.
