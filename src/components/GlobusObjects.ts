import { atom, selector } from 'recoil';

export const ConfigAtom = atom({
  key: 'ConfigAtom',
  default: {
    collection_id: '',
    collection_base_path: '',
    is_gcp: false,
    is_hub: false,
    is_manual_copy_code_required: false,
    is_logged_in: false,
    collection_id_owner: '',
    last_login: null,
  },
});

export const TransferAtom = atom({
  key: 'TransferAtom',
  default: {
    source_endpoint: '',
    destination_endpoint: '',
    transfer_items: [{
      source_path: '',
      destination_path: '',
      recursive: false
    }],
  },
});

export const TransferSelector = selector({
  key: 'TransferSelector',
  get: ({ get }) => {
    return get(TransferAtom);
  },
  set: ({ get, set }, newTransferObject: object) => {
    let oldTransferObject = get(TransferAtom);

    let updatedTransferObject = {
      ...oldTransferObject,
      ...newTransferObject,
    };
    
    set(TransferAtom, updatedTransferObject);
  },
});
