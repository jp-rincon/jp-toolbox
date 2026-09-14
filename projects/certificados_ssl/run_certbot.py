import sys
import os
import shutil
import certbot.compat.misc
import certbot.compat.filesystem

# Desactivar chequeo de administrador y permitir creación estándar de archivos sin requerir ACLs de administrador
certbot.compat.misc.raise_for_non_administrative_windows_rights = lambda: None
certbot.compat.filesystem.open = os.open
certbot.compat.filesystem.chmod = lambda *args, **kwargs: None
certbot.compat.filesystem.copy_ownership_and_apply_mode = lambda *args, **kwargs: None
certbot.compat.filesystem.copy_security = lambda *args, **kwargs: None
certbot.compat.filesystem.check_permissions = lambda *args, **kwargs: True
certbot.compat.filesystem.has_min_permissions = lambda *args, **kwargs: True

# Monkeypatch para soportar almacenamiento en Windows sin privilegios de administrador para symlinks
real_symlink = os.symlink

def windows_safe_symlink(src, dst):
    try:
        real_symlink(src, dst)
    except OSError:
        if not os.path.isabs(src):
            real_src = os.path.normpath(os.path.join(os.path.dirname(dst), src))
        else:
            real_src = src
        if os.path.exists(real_src):
            shutil.copy2(real_src, dst)
        else:
            with open(dst, "wb"):
                pass

os.symlink = windows_safe_symlink

orig_readlink = certbot.compat.filesystem.readlink
def windows_safe_readlink(link_path):
    try:
        return orig_readlink(link_path)
    except (OSError, ValueError):
        fname = os.path.basename(link_path)
        name, ext = os.path.splitext(fname)
        domain = os.path.basename(os.path.dirname(link_path))
        return os.path.abspath(os.path.join(os.path.dirname(link_path), "..", "..", "archive", domain, f"{name}1{ext}"))

certbot.compat.filesystem.readlink = windows_safe_readlink

import certbot._internal.storage as storage

storage.RenewableCert._check_symlinks = lambda self: None
storage.RenewableCert._fix_symlinks = lambda self: None
storage.RenewableCert._consistent = lambda self: True
storage.get_link_target = lambda link: windows_safe_readlink(link)

@classmethod
def windows_new_lineage(cls, lineagename, cert, privkey, chain, cli_config):
    for i in (cli_config.renewal_configs_dir, cli_config.default_archive_dir, cli_config.live_dir):
        if not os.path.exists(i):
            storage.filesystem.makedirs(i, 0o700)

    config_file, config_filename = storage.util.unique_lineage_name(
        cli_config.renewal_configs_dir, lineagename)
    base_readme_path = os.path.join(cli_config.live_dir, storage.README)
    if not os.path.exists(base_readme_path):
        storage._write_live_readme_to(base_readme_path, is_base_dir=True)

    lineagename = storage.lineagename_for_filename(config_filename)
    archive = storage.full_archive_path(None, cli_config, lineagename)
    live_dir = storage._full_live_path(cli_config, lineagename)

    for i in (archive, live_dir):
        if not os.path.exists(i):
            storage.filesystem.makedirs(i)

    target = {kind: os.path.join(live_dir, kind + ".pem") for kind in storage.ALL_FOUR}
    archive_target = {kind: os.path.join(archive, kind + "1.pem") for kind in storage.ALL_FOUR}

    # Escribir directamente los certificados tanto en archive como en live sin requerir symlinks
    for p in (target["cert"], archive_target["cert"]):
        with open(p, "wb") as f:
            f.write(cert)

    for p in (target["privkey"], archive_target["privkey"]):
        with open(p, "wb") as f:
            f.write(privkey)

    for p in (target["chain"], archive_target["chain"]):
        with open(p, "wb") as f:
            f.write(chain)

    for p in (target["fullchain"], archive_target["fullchain"]):
        with open(p, "wb") as f:
            f.write(cert + chain)

    readme_path = os.path.join(live_dir, storage.README)
    storage._write_live_readme_to(readme_path)
    config_file.close()

    storage.create_renewal_config_file(config_filename, archive, target, cli_config)
    return cls(config_filename, cli_config)

storage.RenewableCert.new_lineage = windows_new_lineage

from certbot.main import main

if __name__ == "__main__":
    sys.exit(main())
