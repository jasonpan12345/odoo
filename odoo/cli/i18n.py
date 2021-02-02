import optparse
import os
import sys
import base64

import odoo
from . import Command


class I18n(Command):

    def run(self, cmdargs):
        parser = optparse.OptionParser(
            prog="%s start" % sys.argv[0].split(os.path.sep)[-1],
            description=self.__doc__
        )
        parser.add_option("-d", "--database", dest="db_name", default=None,
                          help="Specify the database name (default to project's directory name")
        parser.add_option('--lang', help="Language to support.")
        parser.add_option('--module', help="Module name to generate.")
        parser.add_option('--addons_path', help="Module path.")

        opt, args = parser.parse_args(cmdargs)

        path_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        path_config_file = os.path.join(path_root, "config.conf")
        lst_addons = []
        with open(path_config_file, "r") as file:
            lst_line = file.readlines()
            lst_ignore_addons = ["/addons/addons", "/image_db"]
            for line in lst_line:
                if "addons_path" in line:
                    lst_path = line[line.find(" = ") + 3:].split(",")
                    for path in lst_path:
                        path = path.strip()
                        if not path:
                            continue
                        is_valid = not any([a in path for a in lst_ignore_addons])
                        if not is_valid:
                            continue
                        lst_addons.append(path)
                    break
        addons = ",".join(lst_addons)
        odoo.tools.config._parse_config([f"--addons-path={addons}"])

        with odoo.api.Environment.manage():
            if not opt.db_name:
                print("Need a db name, check --db_name.")
                return
            registry = odoo.registry(opt.db_name)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                module_id = env["ir.module.module"].search([("name", "=", opt.module), ('state', '=', 'installed')])
                if not module_id:
                    print(f"Module '{opt.module}' not installed.")
                    return
                i18n_path = os.path.join(opt.addons_path, opt.module, "i18n")
                os.makedirs(i18n_path, exist_ok=True)

                export = env["base.language.export"].create({
                    'format': 'po',
                    'modules': [(6, 0, [module_id.id])]
                })
                export.act_getfile()
                po_file = export.data
                data = base64.b64decode(po_file).decode("utf-8")
                translation_file = os.path.join(i18n_path, f"{opt.module}.pot")

                with open(translation_file, "w") as file:
                    file.write(data)

                # Create po
                lang = 'fr_CA'
                translation_file = os.path.join(i18n_path, f"{lang}.po")
                export = env["base.language.export"].create({
                    'lang': lang,
                    'format': 'po',
                    'modules': [(6, 0, [module_id.id])]
                })
                export.act_getfile()
                po_file = export.data
                data = base64.b64decode(po_file).decode("utf-8")

                with open(translation_file, "w") as file:
                    file.write(data)


def die(cond, message, code=1):
    if cond:
        print(message, file=sys.stderr)
        sys.exit(code)
