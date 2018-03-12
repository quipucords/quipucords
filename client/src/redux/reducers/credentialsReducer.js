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
    case helpers.rejectedAction(credentialsTypes.ADD_CREDENTIAL):
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

    case helpers.rejectedAction(credentialsTypes.DELETE_CREDENTIAL):
    case helpers.rejectedAction(credentialsTypes.DELETE_CREDENTIALS):
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

    case helpers.rejectedAction(credentialsTypes.UPDATE_CREDENTIAL):
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

    case helpers.rejectedAction(credentialsTypes.GET_CREDENTIAL):
    case helpers.rejectedAction(credentialsTypes.GET_CREDENTIALS):
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
    case helpers.pendingAction(credentialsTypes.ADD_CREDENTIAL):
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

    case helpers.pendingAction(credentialsTypes.DELETE_CREDENTIAL):
    case helpers.pendingAction(credentialsTypes.DELETE_CREDENTIALS):
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

    case helpers.pendingAction(credentialsTypes.UPDATE_CREDENTIAL):
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

    case helpers.pendingAction(credentialsTypes.GET_CREDENTIAL):
    case helpers.pendingAction(credentialsTypes.GET_CREDENTIALS):
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
    case helpers.fulfilledAction(credentialsTypes.ADD_CREDENTIAL):
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

    case helpers.fulfilledAction(credentialsTypes.DELETE_CREDENTIAL):
    case helpers.fulfilledAction(credentialsTypes.DELETE_CREDENTIALS):
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

    case helpers.fulfilledAction(credentialsTypes.UPDATE_CREDENTIAL):
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

    case helpers.fulfilledAction(credentialsTypes.GET_CREDENTIAL):
    case helpers.fulfilledAction(credentialsTypes.GET_CREDENTIALS):
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
