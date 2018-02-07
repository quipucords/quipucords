import { credentialsTypes } from '../constants';

// ToDo: take a look at a redux form plugin, and/or nesting state to allow resetting parts of it and more concise property names, i.e. { view: {}, updateDialog: {} }
const initialState = {
  credentials: [],

  newCredential: null,
  editCredential: null,
  newCredentialType: '',
  showCreateDialog: false,
  showEditDialog: false,

  addError: false,
  addErrorMessage: '',
  deleteError: false,
  deleteErrorMessage: '',
  getError: false,
  getErrorMessage: '',
  updateError: false,
  updateErrorMessage: '',

  addPending: false,
  deletePending: false,
  getPending: false,
  updatePending: false,

  addFulfilled: false,
  deleteFulfilled: false,
  getFulfilled: false,
  updateFulfilled: false
};

function credentialsReducer(state = initialState, action) {
  switch (action.type) {
    // Show/Hide
    case credentialsTypes.EDIT_CREDENTIAL_SHOW:
      return Object.assign({}, state, {
        showEditDialog: true,
        editCredential: action.credential
      });

    case credentialsTypes.EDIT_CREDENTIAL_HIDE:
      return Object.assign({}, state, {
        showEditDialog: false,
        editCredential: null,
        updateFulfilled: false
      });

    case credentialsTypes.CREATE_CREDENTIAL_SHOW:
      return Object.assign({}, state, {
        showCreateDialog: true,
        newCredentialType: action.newCredentialType
      });

    case credentialsTypes.CREATE_CREDENTIAL_HIDE:
      return Object.assign({}, state, {
        showCreateDialog: false,
        newCredentialType: '',
        newCredential: null,
        addFulfilled: false
      });

    // Error/Rejected
    case credentialsTypes.ADD_CREDENTIAL_REJECTED:
      return Object.assign({}, state, {
        addError: action.payload.error,
        addErrorMessage: action.payload.message,
        addPending: false
      });

    case credentialsTypes.DELETE_CREDENTIAL_REJECTED:
    case credentialsTypes.DELETE_CREDENTIALS_REJECTED:
      return Object.assign({}, state, {
        deleteError: action.payload.error,
        deleteErrorMessage: action.payload.message,
        deletePending: false
      });

    case credentialsTypes.GET_CREDENTIAL_REJECTED:
      return Object.assign({}, state, {
        getError: action.payload.error,
        getErrorMessage: action.payload.message,
        getPending: false
      });

    case credentialsTypes.UPDATE_CREDENTIAL_REJECTED:
      return Object.assign({}, state, {
        updateError: action.payload.error,
        updateErrorMessage: action.payload.message,
        updatePending: false
      });

    // Loading/Pending
    case credentialsTypes.ADD_CREDENTIAL_PENDING:
      return Object.assign({}, state, { addPending: true });

    case credentialsTypes.DELETE_CREDENTIAL_PENDING:
    case credentialsTypes.DELETE_CREDENTIALS_PENDING:
      return Object.assign({}, state, { deletePending: true });

    case credentialsTypes.GET_CREDENTIAL_PENDING:
    case credentialsTypes.GET_CREDENTIALS_PENDING:
      return Object.assign({}, state, { getPending: true });

    case credentialsTypes.UPDATE_CREDENTIAL_PENDING:
      return Object.assign({}, state, { updatePending: true });

    // Success/Fulfilled
    case credentialsTypes.ADD_CREDENTIAL_FULFILLED:
      return Object.assign({}, state, {
        newCredential: action.payload,
        addFulfilled: true,
        addPending: false
      });

    case credentialsTypes.DELETE_CREDENTIAL_FULFILLED:
    case credentialsTypes.DELETE_CREDENTIALS_FULFILLED:
      return Object.assign({}, state, {
        deleteFulfilled: true,
        deletePending: false
      });

    case credentialsTypes.GET_CREDENTIAL_FULFILLED:
    case credentialsTypes.GET_CREDENTIALS_FULFILLED:
      return Object.assign({}, state, {
        credentials: action.payload.results,
        getFulfilled: true,
        getPending: false
      });

    case credentialsTypes.UPDATE_CREDENTIAL_FULFILLED:
      return Object.assign({}, state, {
        editCredential: action.payload,
        updateFulfilled: true,
        updatePending: false
      });

    default:
      return state;
  }
}

export { initialState, credentialsReducer };

export default credentialsReducer;
