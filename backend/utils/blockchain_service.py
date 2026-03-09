import json
import paramiko
import shlex
import re

CHANNEL = "mychannel"
CHAINCODE = "basic"

# -----------------------------
# EC2 CONNECTION DETAILS
# -----------------------------

EC2_HOST = "43.205.92.85"
EC2_USER = "ubuntu"
EC2_KEY = r"D:\src\Final Year Research\blockchain\blockchain-ledger-key.pem"


# ------------------------------------------------
# EXECUTE COMMAND ON EC2
# ------------------------------------------------

def run_command(cmd):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        hostname=EC2_HOST,
        username=EC2_USER,
        key_filename=EC2_KEY
    )

    cmd_string = " ".join(cmd)

    full_command = f"""
cd ~/fabric-samples/test-network
export PATH=$PATH:~/fabric-samples/bin
export FABRIC_CFG_PATH=~/fabric-samples/config
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_ADDRESS=localhost:7051
export CORE_PEER_TLS_ROOTCERT_FILE=~/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=~/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp

{cmd_string}
"""

    command = f"bash -lc {shlex.quote(full_command)}"

    print("Executing:", cmd_string)

    stdin, stdout, stderr = ssh.exec_command(command)

    output = stdout.read().decode()
    error = stderr.read().decode()

    ssh.close()

    if "Error:" in error:
        raise Exception(error)

    return output.strip() if output else error.strip()


# ------------------------------------------------
# EXTRACT TX HASH FROM FABRIC RESPONSE
# ------------------------------------------------

def extract_tx_hash(cli_output):

    """
    Fabric returns txid in invoke output.
    This function extracts it.
    """

    match = re.search(r"txid:\s*([a-zA-Z0-9]+)", cli_output)

    if match:
        return match.group(1)

    return None


# ------------------------------------------------
# REGISTER PART ON BLOCKCHAIN
# ------------------------------------------------

def register_part(data):

    payload = json.dumps({
        "Args": [
            "RegisterPart",
            data["serialNumber"],
            data["partID"],
            data["blockchainID"],
            data["manufacturer"],
            data["country"],
            data["owner"],
            data["mintedAt"],
            str(data["refurbished"]).lower(),
            data["txHash"]
        ]
    })

    cmd = [
        "peer", "chaincode", "invoke",
        "-o", "localhost:7050",
        "--ordererTLSHostnameOverride", "orderer.example.com",
        "--tls",
        "--cafile",
        "~/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
        "-C", CHANNEL,
        "-n", CHAINCODE,

        "--peerAddresses", "localhost:7051",
        "--tlsRootCertFiles",
        "~/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt",

        "--peerAddresses", "localhost:9051",
        "--tlsRootCertFiles",
        "~/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt",

        "-c", f"'{payload}'"
    ]

    result = run_command(cmd)

    tx_hash = extract_tx_hash(result)

    return {
        "result": result,
        "tx_hash": tx_hash
    }


# ------------------------------------------------
# VERIFY PART FROM BLOCKCHAIN
# ------------------------------------------------

def verify_part(serial):

    payload = json.dumps({
        "Args": ["VerifyPart", serial]
    })

    cmd = [
        "peer", "chaincode", "query",
        "-C", CHANNEL,
        "-n", CHAINCODE,
        f"-c '{payload}'"
    ]

    result = run_command(cmd)

    if not result:
        return None

    try:
        return json.loads(result)
    except:
        return {"raw": result}


# ------------------------------------------------
# TRANSFER OWNERSHIP
# ------------------------------------------------

def transfer_part(serial, new_owner):

    payload = json.dumps({
        "Args": [
            "TransferOwnership",
            serial,
            new_owner
        ]
    })

    cmd = [
        "peer", "chaincode", "invoke",
        "-o", "localhost:7050",
        "--ordererTLSHostnameOverride", "orderer.example.com",
        "--tls",
        "--cafile",
        "~/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
        "-C", CHANNEL,
        "-n", CHAINCODE,

        "--peerAddresses", "localhost:7051",
        "--tlsRootCertFiles",
        "~/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt",

        "--peerAddresses", "localhost:9051",
        "--tlsRootCertFiles",
        "~/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt",

        "-c", f"'{payload}'"
    ]

    result = run_command(cmd)

    tx_hash = extract_tx_hash(result)

    return {
        "result": result,
        "tx_hash": tx_hash
    }