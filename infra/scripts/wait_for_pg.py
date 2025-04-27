import subprocess
import time


def _check_postgres():
    try:
        result = subprocess.run(
            ["docker", "exec", "postgres-dev", "pg_isready", "--host", "localhost"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if "accepting connections" not in result.stdout:
            print(".", end="", flush=True)
            time.sleep(1)
            _check_postgres()
        else:
            print("\n🟢 Postgres está pronto e aceitando conexões")
    except Exception as e:
        print(f"\n🔴 Ocorreu um erro: {e}")


print("\n🔴 Aguardando Postgres aceitar conexões", end="", flush=True)
_check_postgres()
