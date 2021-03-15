import optparse
import os
import sys

import odoo
from . import Command
from odoo.service import db
from odoo.http import dispatch_rpc


class Db(Command):

    def run(self, cmdargs):
        parser = optparse.OptionParser(
            prog="%s start" % sys.argv[0].split(os.path.sep)[-1],
            description=self.__doc__
        )
        parser.add_option("-d", "--database", dest="db_name", default=None,
                          help="Specify the database name (default to project's directory name)")
        parser.add_option("--from_database", dest="db_name_from", default=None,
                          help="Specify the database name to clone from.")
        parser.add_option('--restore_db_file', help="Path of file to restore")
        parser.add_option('--restore_image', help="Image name from ERPLibre/image_db")
        parser.add_option('--master_password', help="Specify the master password if need it.")

        # group = optparse.OptionGroup(parser, "Command")
        parser.add_option("--drop", action="store_true", help="Command drop database.")
        parser.add_option("--clone", action="store_true", help="Command clone database.")
        parser.add_option("--restore", action="store_true", help="Command restore database.")
        parser.add_option("--list", action="store_true", help="Command list database.")
        parser.add_option("--list_incompatible_db", action="store_true", help="Command list database incompatible.")
        parser.add_option("--version", action="store_true", help="Command show odoo version.")

        opt, args = parser.parse_args(cmdargs)

        die(bool(opt.drop) and bool(opt.restore) and bool(opt.list) and bool(opt.version) and bool(
            opt.list_incompatible_db),
            "Can only run one command, --drop, --list, --version, --list_incompatible_db or --restore.")

        die(bool(opt.restore) and not (bool(opt.restore_db_file) or bool(opt.restore_image)),
            "Missing argument --restore_db_file or --restore_image of option --restore.")

        die(bool(opt.restore) and not bool(opt.db_name),
            "Missing argument --database of option --restore.")

        die(bool(opt.clone) and not bool(opt.db_name),
            "Missing argument --database of option --clone.")

        die(bool(opt.clone) and not bool(opt.db_name_from),
            "Missing argument --from_database of option --clone.")

        die(bool(opt.drop) and not bool(opt.db_name),
            "Missing argument --database of option --drop.")

        die(bool(opt.restore_db_file) and bool(opt.restore_image),
            "Cannot support both argument --restore_db_file and --restore_image")

        with odoo.api.Environment.manage():
            if opt.list:
                lst_db = db.list_dbs()
                for db_obj in lst_db:
                    print(db_obj)
            elif opt.list_incompatible_db:
                lst_db = db.list_db_incompatible(db.list_dbs())
                for db_obj in lst_db:
                    print(db_obj)
            elif opt.drop:
                master_password = opt.master_password if opt.master_password else 'admin'
                dispatch_rpc('db', 'drop', [master_password, opt.db_name])
            elif opt.restore:
                if opt.restore_image:
                    file_name = opt.restore_image if opt.restore_image.endswith(".zip") else f"{opt.restore_image}.zip"
                    file_path = os.path.join(".", "image_db", file_name)
                    db.restore_db(opt.db_name, file_path, False)
                elif opt.restore_db_file:
                    db.restore_db(opt.db_name, opt.restore_db_file, False)
            elif opt.clone:
                db.exp_duplicate_database(opt.db_name_from, opt.db_name)
            elif opt.version:
                print(db.exp_server_version())
            else:
                parser.print_help(sys.stderr)
                die(True, "ERROR, missing command")


def die(cond, message, code=1):
    if cond:
        print(message, file=sys.stderr)
        sys.exit(code)
