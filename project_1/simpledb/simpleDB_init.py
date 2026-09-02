import boto3
import pandas as pd

SIMPLEDB_DOMAIN_NAME = "<ASU_ID>-simpleDB"
CLASSIFICATION_FILE_PATH = "./Classification Results on Face Dataset (1000 images).csv"

def main():
    # Uses the default boto3 credential chain (env vars, ~/.aws/credentials, or an IAM role).
    simpledb_client = boto3.client(
        "sdb",
        region_name="us-east-1"
    )

    # Reading file with classifcation results
    results_df = pd.read_csv(CLASSIFICATION_FILE_PATH)

    # domains_list = simpledb_client.list_domains()
    # try:
    #     if SIMPLEDB_DOMAIN_NAME in domains_list["DomainNames"]:
    #         response = simpledb_client.delete_domain(
    #             DomainName=SIMPLEDB_DOMAIN_NAME
    #         )
    #         print(f"Delete domain response: {response}")
    # except Exception as e:
    #     print(f"\'{SIMPLEDB_DOMAIN_NAME}\' domain doesn't exist.")
    
    # # Creating Domain in SimpleDB
    # try:
    #     simpledb_client.create_domain(
    #         DomainName=SIMPLEDB_DOMAIN_NAME
    #     )
    #     print(f"Created domain \"{SIMPLEDB_DOMAIN_NAME}\".")

    #     domains_list = simpledb_client.list_domains()
    #     print("Domains:")
    #     print(domains_list["DomainNames"])
    # except Exception as e:
    #     print(f"{e}")
    #     print(f"Failed to create domain \"{SIMPLEDB_DOMAIN_NAME}\".")
    #     return

    # # Storing classification results in SimpleDB.
    # print(f"\nStoring in SimpleDB:")
    # for _, row in results_df.iterrows():
    #     try:
    #         response = simpledb_client.put_attributes(
    #             DomainName=SIMPLEDB_DOMAIN_NAME,
    #             ItemName=row["Image"],
    #             Attributes=[
    #                 {
    #                     'Name': 'Results',
    #                     'Value': row["Results"],
    #                     'Replace': True
    #                 }
    #             ],
    #         )
    #         print(f"Storing {row['Image']} response: {response}")
    #     except Exception as e:
    #         print(e)
    #         print(f"Failed to save result for {row["Image"]}.")

    # Checking if all values were stored
    print("\nChecking SimpleDB:")
    for _, row in results_df.iterrows():
        try:
            response = simpledb_client.get_attributes(
                DomainName=SIMPLEDB_DOMAIN_NAME,
                ItemName=row["Image"],
                AttributeNames=[
                    'Results'
                ],
                ConsistentRead=True
            )
            
            if response["Attributes"][0]["Value"] != row["Results"]:
                print(f"Results not matching for {row['Image']}")
        except Exception as e:
            print(e)
            print(f"Could not find result for {row["Image"]}.")

if __name__ == "__main__":
    main()