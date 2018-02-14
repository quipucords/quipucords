import _ from 'lodash';
import helpers from '../../common/helpers';
import { credentialsTypes } from '../constants';

const initialState = {
  persist: {
    selectedCredentials: []
  },

  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    credentials: []
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    credential: null,
    credentialType: '',
    show: false,
    add: false,
    edit: false,
    delete: false
  }
};

const selectedIndex = function(state, credential) {
  return _.findIndex(state.persist.selectedCredentials, nextSelected => {
    return nextSelected.id === _.get(credential, 'id');
  });
};

const credentialsReducer = function(state = initialState, action) {
  switch (action.type) {
    // Persist
    case credentialsTypes.SELECT_CREDENTIAL:
      // Do nothing if it is already selected
      if (selectedIndex(state, action.credential) !== -1) {
        return state;
      }

      action.credential.selected = true;

      const addedSelections = Object.assign({}, state.persist, {
        selectedCredentials: [
          ...state.persist.selectedCredentials,
          action.credential
        ]
      });
      return Object.assign({}, state, { persist: addedSelections });

    case credentialsTypes.DESELECT_CREDENTIAL:
      const index = selectedIndex(state, action.credential);

      // Do nothing if it is not already selected
      if (index === -1) {
        return state;
      }

      action.credential.selected = false;

      const removedSelections = Object.assign({}, state.persist, {
        selectedCredentials: [
          ...state.persist.selectedCredentials.slice(0, index),
          ...state.persist.selectedCredentials.slice(index + 1)
        ]
      });
      return Object.assign({}, state, { persist: removedSelections });

    // Show/Hide
    case credentialsTypes.CREATE_CREDENTIAL_SHOW:
      return helpers.setStateProp(
        'update',
        {
          show: true,
          add: true,
          credentialType: action.credentialType
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.EDIT_CREDENTIAL_SHOW:
      return helpers.setStateProp(
        'update',
        {
          show: true,
          edit: true,
          credential: action.credential
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.UPDATE_CREDENTIAL_HIDE:
      return helpers.setStateProp(
        'update',
        {
          show: false
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case credentialsTypes.ADD_CREDENTIAL_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: _.get(
            action.payload,
            'response.request.responseText',
            action.payload.message
          ),
          add: true,
          show: state.update.show
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.DELETE_CREDENTIAL_REJECTED:
    case credentialsTypes.DELETE_CREDENTIALS_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: _.get(
            action.payload,
            'response.request.responseText',
            action.payload.message
          ),
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.UPDATE_CREDENTIAL_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: action.payload.message,
          edit: true,
          show: state.update.show
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.GET_CREDENTIAL_REJECTED:
    case credentialsTypes.GET_CREDENTIALS_REJECTED:
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
          errorMessage: action.payload.message
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case credentialsTypes.ADD_CREDENTIAL_PENDING:
      return helpers.setStateProp(
        'update',
        {
          pending: true,
          add: true,
          show: state.update.show
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.DELETE_CREDENTIAL_PENDING:
    case credentialsTypes.DELETE_CREDENTIALS_PENDING:
      return helpers.setStateProp(
        'update',
        {
          pending: true,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.UPDATE_CREDENTIAL_PENDING:
      return helpers.setStateProp(
        'update',
        {
          pending: true,
          edit: true,
          show: state.update.show
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.GET_CREDENTIAL_PENDING:
    case credentialsTypes.GET_CREDENTIALS_PENDING:
      return helpers.setStateProp(
        'view',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case credentialsTypes.ADD_CREDENTIAL_FULFILLED:
      return helpers.setStateProp(
        'update',
        {
          credential: action.payload,
          fulfilled: true,
          add: true
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.DELETE_CREDENTIAL_FULFILLED:
    case credentialsTypes.DELETE_CREDENTIALS_FULFILLED:
      return helpers.setStateProp(
        'update',
        {
          credential: action.payload,
          fulfilled: true,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.UPDATE_CREDENTIAL_FULFILLED:
      return helpers.setStateProp(
        'update',
        {
          credential: action.payload,
          fulfilled: true,
          edit: true
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.GET_CREDENTIAL_FULFILLED:
    case credentialsTypes.GET_CREDENTIALS_FULFILLED:
      // Get resulting credentials and update the selected state of each
      const credentials = _.get(action, 'payload.data.results', []).map(
        nextCredential => {
          return {
            ...nextCredential,
            selected: selectedIndex(state, nextCredential) !== -1
          };
        }
      );
      return helpers.setStateProp(
        'view',
        {
          credentials: credentials,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.UPDATE_CREDENTIAL_RESET_STATUS:
      return helpers.setStateProp(
        'update',
        {
          error: false,
          errorMessage: ''
        },
        {
          state
        }
      );

    default:
      return state;
  }
};

export { initialState, credentialsReducer };

export default credentialsReducer;
