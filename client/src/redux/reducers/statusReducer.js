import { statusTypes } from '../constants';
import helpers from '../../common/helpers';

const initialState = {
  error: false,
  errorMessage: '',
  pending: false,
  fulfilled: false,
  currentStatus: {}
};

const statusReducer = (state = initialState, action) => {
  switch (action.type) {
    case helpers.REJECTED_ACTION(statusTypes.STATUS_INFO):
      return {
        ...initialState,
        error: action.error,
        errorMessage: helpers.getMessageFromResults(action.payload).message
      };

    case helpers.PENDING_ACTION(statusTypes.STATUS_INFO):
      return {
        ...initialState,
        pending: true
      };

    case helpers.FULFILLED_ACTION(statusTypes.STATUS_INFO):
      return {
        ...initialState,
        currentStatus: action.payload.data,
        fulfilled: true
      };

    default:
      return state;
  }
};

statusReducer.initialState = initialState;

export { statusReducer as default, initialState, statusReducer };
