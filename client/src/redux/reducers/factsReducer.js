import helpers from '../../common/helpers';
import { factsTypes } from '../constants';

const initialState = {
  persist: {},

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    facts: {}
  }
};

const factsReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case factsTypes.ADD_FACTS_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.payload.error,
          errorMessage: action.payload.message
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case factsTypes.ADD_FACTS_PENDING:
      return helpers.setStateProp(
        'update',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case factsTypes.ADD_FACTS_FULFILLED:
      return helpers.setStateProp(
        'update',
        {
          facts: action.payload,
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

export { initialState, factsReducer };

export default factsReducer;
