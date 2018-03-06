import _ from 'lodash';
import helpers from '../../common/helpers';
import { credentialsTypes } from '../constants';

const initialState = {
  persist: {
    selectedCredentials: [],
    expandedCredentials: []
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

const expandedIndex = function(state, credential) {
  return _.findIndex(state.persist.expandedCredentials, nextSelected => {
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

      return helpers.setStateProp(
        'persist',
        {
          selectedCredentials: [...state.persist.selectedCredentials, action.credential]
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.DESELECT_CREDENTIAL:
      const index = selectedIndex(state, action.credential);
      // Do nothing if it is not already selected
      if (index === -1) {
        return state;
      }

      return helpers.setStateProp(
        'persist',
        {
          selectedCredentials: [
            ...state.persist.selectedCredentials.slice(0, index),
            ...state.persist.selectedCredentials.slice(index + 1)
          ]
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.EXPAND_CREDENTIAL:
      const expandIndex = expandedIndex(state, action.credential);
      let newExpansions;

      if (expandIndex === -1) {
        newExpansions = [...state.persist.expandedCredentials];
      } else {
        newExpansions = [
          ...state.persist.expandedCredentials.slice(0, expandIndex),
          ...state.persist.expandedCredentials.slice(expandIndex + 1)
        ];
      }

      if (action.expandType) {
        newExpansions.push({
          id: action.credential.id,
          expandType: action.expandType
        });
      }

      return helpers.setStateProp(
        'persist',
        {
          expandedCredentials: newExpansions
        },
        {
          state,
          reset: false
        }
      );

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
          errorMessage: helpers.getErrorMessageFromResults(action.payload),
          pending: false,
          add: true
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.DELETE_CREDENTIAL_REJECTED:
    case credentialsTypes.DELETE_CREDENTIALS_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload),
          delete: true,
          pending: false
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.UPDATE_CREDENTIAL_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload),
          pending: false,
          edit: true
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.GET_CREDENTIAL_REJECTED:
    case credentialsTypes.GET_CREDENTIALS_REJECTED:
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
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
          error: false,
          fulfilled: false
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.DELETE_CREDENTIAL_PENDING:
    case credentialsTypes.DELETE_CREDENTIALS_PENDING:
      return helpers.setStateProp(
        'update',
        {
          pending: true,
          delete: true,
          error: false,
          fulfilled: false
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.UPDATE_CREDENTIAL_PENDING:
      return helpers.setStateProp(
        'update',
        {
          pending: true,
          error: false,
          fulfilled: false
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.GET_CREDENTIAL_PENDING:
    case credentialsTypes.GET_CREDENTIALS_PENDING:
      return helpers.setStateProp(
        'view',
        {
          pending: true,
          credentials: state.view.credentials
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
          pending: false,
          error: false,
          errorMessage: ''
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.DELETE_CREDENTIAL_FULFILLED:
    case credentialsTypes.DELETE_CREDENTIALS_FULFILLED:
      return helpers.setStateProp(
        'update',
        {
          credential: action.payload,
          fulfilled: true,
          pending: false,
          delete: true,
          error: false,
          errorMessage: ''
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.UPDATE_CREDENTIAL_FULFILLED:
      return helpers.setStateProp(
        'update',
        {
          credential: action.payload,
          fulfilled: true,
          pending: false,
          error: false,
          errorMessage: ''
        },
        {
          state,
          reset: false
        }
      );

    case credentialsTypes.GET_CREDENTIAL_FULFILLED:
    case credentialsTypes.GET_CREDENTIALS_FULFILLED:
      return helpers.setStateProp(
        'view',
        {
          credentials: _.get(action, 'payload.data.results', []),
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case credentialsTypes.GET_WIZARD_CREDENTIALS_FULFILLED:
      return helpers.setStateProp(
        'view',
        {
          credentials: _.get(action, 'payload.data.results', []),
          pending: false
        },
        {
          state,
          reset: false
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
          state,
          reset: false
        }
      );

    default:
      return state;
  }
};

export { initialState, credentialsReducer };

export default credentialsReducer;
