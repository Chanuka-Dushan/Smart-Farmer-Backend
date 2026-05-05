import psycopg2
from psycopg2.extras import RealDictCursor

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def normalize_owner_identifier(value):
    if value is None:
        return value

    return str(value).strip().lower()


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    db_url = DATABASE_URL

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return psycopg2.connect(
        db_url,
        sslmode="require"
    )


# -----------------------------------------
# SAVE PART METADATA
# -----------------------------------------

def save_part_metadata(data):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO part_metadata
    (
        serial_number,
        part_id,
        part_name,
        manufacturer,
        country,
        description,
        current_owner,
        blockchain_registered,
        qr_generated,
        transfer_requested,
        transfer_status
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,false,false,false,'NONE')
    """

    cursor.execute(query, (
        data["serialNumber"],
        data["partID"],
        data["partName"],
        data["manufacturer"],
        data["country"],
        data["description"],
        normalize_owner_identifier(data["owner"])
    ))

    conn.commit()

    cursor.close()
    conn.close()

# -----------------------------------------
# GET PART METADATA
# -----------------------------------------

def get_part_metadata(serial):

    conn = get_connection()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM part_metadata WHERE serial_number=%s",
        (serial,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result


# -----------------------------------------
# UPDATE BLOCKCHAIN REGISTRATION
# -----------------------------------------

def update_blockchain_registration(serial, tx_hash):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    UPDATE part_metadata
    SET
        blockchain_registered = true,
        qr_generated = true,
        blockchain_tx_hash = %s
    WHERE serial_number = %s
    """

    cursor.execute(query, (tx_hash, serial))

    conn.commit()

    cursor.close()
    conn.close()


# -----------------------------------------
# GET ALL PARTS
# -----------------------------------------

def get_all_parts():

    conn = get_connection()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM part_metadata")

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results


# -----------------------------------------
# GET BLOCKCHAIN REGISTERED PARTS
# -----------------------------------------

def get_blockchain_registered_parts():

    conn = get_connection()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        """
        SELECT *
        FROM part_metadata
        WHERE blockchain_registered = true
        """
    )

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results if results else []


# ------------------------------------------------
# CREATE TRANSFER REQUEST
# ------------------------------------------------

def request_transfer(serial, buyer):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    UPDATE part_metadata
    SET
        transfer_requested = true,
        requested_new_owner = %s,
        transfer_status = 'PENDING'
    WHERE serial_number = %s
    """

    cursor.execute(query, (normalize_owner_identifier(buyer), serial))

    conn.commit()

    cursor.close()
    conn.close()


# ------------------------------------------------
# GET PENDING REQUESTS FOR SELLER
# ------------------------------------------------

def get_pending_transfers(owner):

    conn = get_connection()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT *
    FROM part_metadata
    WHERE current_owner = %s
    AND transfer_status = 'PENDING'
    """

    cursor.execute(query, (normalize_owner_identifier(owner),))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results if results else []


# ------------------------------------------------
# APPROVE TRANSFER REQUEST
# ------------------------------------------------

def approve_transfer(serial, new_owner):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    UPDATE part_metadata
    SET
        current_owner = %s,
        transfer_requested = false,
        requested_new_owner = NULL,
        transfer_status = 'APPROVED'
    WHERE serial_number = %s
    """

    cursor.execute(query, (normalize_owner_identifier(new_owner), serial))

    conn.commit()

    cursor.close()
    conn.close()

