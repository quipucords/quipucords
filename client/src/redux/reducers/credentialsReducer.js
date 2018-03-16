import _ from 'lodash';
import helpers from '../../common/helpers';
import { credentialsTypes } from '../constants';

const initialState = {
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

const credentialsReducer = function(state = initialState, action) {
  switch (action.type) {
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
    case helpers.REJECTED_ACTION(credentialsTypes.ADD_CREDENTIAL):
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

    case helpers.REJECTED_ACTION(credentialsTypes.DELETE_CREDENTIAL):
    case helpers.REJECTED_ACTION(credentialsTypes.DELETE_CREDENTIALS):
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

    case helpers.REJECTED_ACTION(credentialsTypes.UPDATE_CREDENTIAL):
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

    case helpers.REJECTED_ACTION(credentialsTypes.GET_CREDENTIAL):
    case helpers.REJECTED_ACTION(credentialsTypes.GET_CREDENTIALS):
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
    case helpers.PENDING_ACTION(credentialsTypes.ADD_CREDENTIAL):
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

    case helpers.PENDING_ACTION(credentialsTypes.DELETE_CREDENTIAL):
    case helpers.PENDING_ACTION(credentialsTypes.DELETE_CREDENTIALS):
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

    case helpers.PENDING_ACTION(credentialsTypes.UPDATE_CREDENTIAL):
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

    case helpers.PENDING_ACTION(credentialsTypes.GET_CREDENTIAL):
    case helpers.PENDING_ACTION(credentialsTypes.GET_CREDENTIALS):
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
    case helpers.FULFILLED_ACTION(credentialsTypes.ADD_CREDENTIAL):
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

    case helpers.FULFILLED_ACTION(credentialsTypes.DELETE_CREDENTIAL):
    case helpers.FULFILLED_ACTION(credentialsTypes.DELETE_CREDENTIALS):
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

    case helpers.FULFILLED_ACTION(credentialsTypes.UPDATE_CREDENTIAL):
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

    case helpers.FULFILLED_ACTION(credentialsTypes.GET_CREDENTIAL):
    case helpers.FULFILLED_ACTION(credentialsTypes.GET_CREDENTIALS):
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
