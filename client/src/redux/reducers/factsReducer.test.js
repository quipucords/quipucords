import { factsTypes } from '../constants';
import factsReducer from './factsReducer';

describe('FactsReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      error: false,
      errorMessage: '',
      loading: true,
      data: {}
    };

    expect(factsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle ADD_FACTS_ERROR', () => {
    const dispatched = {
      type: factsTypes.ADD_FACTS_ERROR,
      error: true,
      message: 'error message'
    };

    expect(factsReducer(undefined, dispatched).error).toEqual(dispatched.error);
    expect(factsReducer(undefined, dispatched).errorMessage).toEqual(
      dispatched.message
    );
  });

  it('should handle ADD_FACTS_LOADING', () => {
    const dispatched = {
      type: factsTypes.ADD_FACTS_LOADING,
      loading: false
    };

    expect(factsReducer(undefined, dispatched).loading).toEqual(
      dispatched.loading
    );
  });

  it('should handle ADD_FACTS_SUCCESS', () => {
    const dispatched = {
      type: factsTypes.ADD_FACTS_SUCCESS,
      data: { test: true }
    };

    expect(factsReducer(undefined, dispatched).data).toEqual(dispatched.data);
  });
});
