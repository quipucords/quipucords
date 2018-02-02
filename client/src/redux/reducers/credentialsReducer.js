import { credentialsTypes } from '../constants';

const initialState = {
  error: false,
  errorMessage: '',
  loading: true,
  data: [],
  showCreateDialog: false,
  createCredentialType: '',
  addLoading: false,
  addError: false,
  addErrorMessage: '',
  newData: null
};

export default function credentialsReducer(state = initialState, action) {
  switch (action.type) {
    case credentialsTypes.GET_CREDENTIALS_ERROR:
      return Object.assign({}, state, {
        error: action.error,
        errorMessage: action.message
      });

    case credentialsTypes.GET_CREDENTIALS_LOADING:
      return Object.assign({}, state, { loading: action.loading });

    case credentialsTypes.GET_CREDENTIALS_SUCCESS:
      return Object.assign({}, state, { data: action.data });

    case credentialsTypes.CREATE_CREDENTIAL_SHOW:
      return Object.assign({}, state, {
        showCreateDialog: true,
        createCredentialType: action.credentialType
      });
    case credentialsTypes.CREATE_CREDENTIAL_HIDE:
      return Object.assign({}, state, { showCreateDialog: false });

    case credentialsTypes.ADD_CREDENTIAL_LOADING:
      return Object.assign({}, state, { addLoading: action.loading });

    case credentialsTypes.ADD_CREDENTIAL_SUCCESS:
      return Object.assign({}, state, { newData: action.data });

    case credentialsTypes.ADD_CREDENTIAL_ERROR:
      return Object.assign({}, state, {
        addError: action.error,
        addErrorMessage: action.message
      });

    default:
      return state;
  }
}
