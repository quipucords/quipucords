import helpers from '../../common/helpers';
import { credentialsTypes } from '../constants';
import apiTypes from '../../constants/apiConstants';

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

const credentialsReducer = (state = initialState, action) => {
  switch (action.type) {
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

    case helpers.REJECTED_ACTION(credentialsTypes.ADD_CREDENTIAL):
      return helpers.setStateProp(
        'update',
        {
          add: true,
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload).message,
          pending: false
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
          errorMessage: helpers.getMessageFromResults(action.payload).message,
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
          errorMessage: helpers.getMessageFromResults(action.payload).message,
          pending: false,
          edit: true
        },
        {
          state,
          reset: false
        }
      );

    case helpers.REJECTED_ACTION(credentialsTypes.GET_CREDENTIALS):
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload).message
        },
        {
          state,
          initialState
        }
      );

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

    case helpers.FULFILLED_ACTION(credentialsTypes.ADD_CREDENTIAL):
      return helpers.setStateProp(
        'update',
        {
          add: true,
          credential: action.payload.data || {},
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(credentialsTypes.DELETE_CREDENTIAL):
    case helpers.FULFILLED_ACTION(credentialsTypes.DELETE_CREDENTIALS):
      return helpers.setStateProp(
        'update',
        {
          delete: true,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(credentialsTypes.UPDATE_CREDENTIAL):
      return helpers.setStateProp(
        'update',
        {
          credential: action.payload.data || {},
          edit: true,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(credentialsTypes.GET_CREDENTIALS):
      return helpers.setStateProp(
        'view',
        {
          credentials: (action.payload.data && action.payload.data[apiTypes.API_RESPONSE_CREDENTIALS_RESULTS]) || [],
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    default:
      return state;
  }
};

credentialsReducer.initialState = initialState;

export { credentialsReducer as default, initialState, credentialsReducer };
