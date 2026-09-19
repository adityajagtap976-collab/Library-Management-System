import argparse
import asyncio
import getpass
import os
import sys

import oracledb
from lms_api.core.security import hash_password


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an active library staff account"
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    return parser.parse_args()


async def create_admin(args: argparse.Namespace, password: str) -> None:
    pool = oracledb.create_pool_async(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
        min=1,
        max=1,
        increment=1,
    )
    try:
        async with pool.acquire() as connection:
            cursor = await connection.cursor()
            try:
                await cursor.execute(
                    """
                    INSERT INTO staff (
                        first_name, last_name, email, password_hash
                    ) VALUES (
                        :first_name, :last_name, :email, :password_hash
                    )
                    """,
                    first_name=args.first_name.strip(),
                    last_name=args.last_name.strip(),
                    email=args.email.strip(),
                    password_hash=hash_password(password),
                )
                await connection.commit()
            finally:
                await cursor.close()
    except oracledb.DatabaseError as error:
        database_error = error.args[0] if error.args else None
        if getattr(database_error, "code", None) == 1:
            print("A staff with this email already exists.", file=sys.stderr)
            return
        raise
    finally:
        await pool.close()

    print(f"Created staff account for {args.email.strip()}.")


def main() -> None:
    args = parse_args()
    password = getpass.getpass("Staff password: ")
    asyncio.run(create_admin(args, password))


if __name__ == "__main__":
    main()
