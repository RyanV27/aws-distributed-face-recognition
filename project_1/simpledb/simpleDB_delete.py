import boto3

SIMPLEDB_DOMAIN_NAME = "<ASU_ID>-simpleDB"

def main():
    # Uses the default boto3 credential chain (env vars, ~/.aws/credentials, or an IAM role).
    simpledb_client = boto3.client(
        "sdb",
        region_name="us-east-1"
    )

    print("Domains before deletion:")
    domains_list = simpledb_client.list_domains()
    print(f"{domains_list}")

    try:
        if SIMPLEDB_DOMAIN_NAME in domains_list["DomainNames"]:
            response = simpledb_client.delete_domain(
                DomainName=SIMPLEDB_DOMAIN_NAME
            )
            print(f"\nDelete domain response: {response}")
    except Exception as e:
        print(f"\'{SIMPLEDB_DOMAIN_NAME}\' domain doesn't exist.")

    print("\nDomains after deletion:")
    domains_list = simpledb_client.list_domains()
    print(f"{domains_list}")

if __name__ == "__main__":
    main()