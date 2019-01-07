import { userTypes } from '../constants';
import helpers from '../../common/helpers';

const initialState = {
  session: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    loggedIn: false,
    authToken: null,
    wasLoggedIn: false
  },
  user: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    currentUser: {}
  }
};

const userReducer = (state = initialState, action) => {
  switch (action.type) {
    // Error/Rejected
    case helpers.REJECTED_ACTION(userTypes.USER_INFO):
      return helpers.setStateProp(
        'user',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(userTypes.USER_INFO):
      return helpers.setStateProp(
        'user',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.FULFILLED_ACTION(userTypes.USER_INFO):
      return helpers.setStateProp(
        'user',
        {
          currentUser: action.payload.data,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.REJECTED_ACTION(userTypes.USER_AUTH):
      return helpers.setStateProp(
        'session',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload),
          wasLoggedIn: state.session.wasLoggedIn
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(userTypes.USER_AUTH):
      return helpers.setStateProp(
        'session',
        {
          pending: true,
          wasLoggedIn: state.session.wasLoggedIn
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.FULFILLED_ACTION(userTypes.USER_AUTH):
      return helpers.setStateProp(
        'session',
        {
          loggedIn: true,
          fulfilled: true,
          wasLoggedIn: true,
          authToken: action.payload.authToken
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.REJECTED_ACTION(userTypes.USER_LOGOUT):
      return helpers.setStateProp(
        'session',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload),
          wasLoggedIn: state.session.wasLoggedIn
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(userTypes.USER_LOGOUT):
      return helpers.setStateProp(
        'session',
        {
          pending: true,
          wasLoggedIn: state.session.wasLoggedIn
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.FULFILLED_ACTION(userTypes.USER_LOGOUT):
      return helpers.setStateProp(
        'session',
        {
          loggedIn: false,
          fulfilled: true,
          wasLoggedIn: state.session.wasLoggedIn
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

userReducer.initialState = initialState;

export { userReducer as default, initialState, userReducer };
