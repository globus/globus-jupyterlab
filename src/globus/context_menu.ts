// import {Dialog, showDialog} from "@jupyterlab/apputils";
import {IFileBrowserFactory} from "@jupyterlab/filebrowser";
import Path from 'Path'

const GLOBUS_LOGO_SMALL = 'jp-Globus-logo-small';
const GLOBUS_WEBAPP_URL = 'https://app.globus.org/file-manager';


export class GlobusContextMenu {
        private serverRoot: String
        private factory: IFileBrowserFactory;
        public options = {
            label: 'Transfer',
            caption: "Example context menu button for file browser's items.",
            icon: GLOBUS_LOGO_SMALL,
            execute: () => {
                return this.contextMenuTransfer()
            },
        }

        constructor(serverRoot: String, factory: IFileBrowserFactory) {
            console.log(factory)
            this.serverRoot = serverRoot
            this.factory = factory
        }

        private static getWebappURL(originID, originPath, destinationID, destinationPath) {
            let webappParams = {
                'origin_id': originID,
                'origin_path': originPath,
                'destination_id': destinationID,
                'destination_path': destinationPath,
            }
            let params = new URLSearchParams(webappParams)
            return GLOBUS_WEBAPP_URL + '?' + params
        }

        public contextMenuTransfer() {

            const file = this.factory.tracker.currentWidget.selectedItems().next();
            const dir = Path.join(this.serverRoot, Path.dirname(file.path))
            const url = GlobusContextMenu.getWebappURL('00d9d1bc-6d51-11eb-8c42-0eb1aa8d4337', dir, '', '')
            window.open(url, 'Globus Transfer', 'height=600,width=800').focus();
        }
}
