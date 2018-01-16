import { factsTypes as types } from '../constants';
import * as actions from './factsActions';

describe('FactsActions', function() {
  it('should create a POST error action', () => {
    const error = true;
    const expectedAction = {
      type: types.ADD_FACTS_ERROR,
      error,
      message: undefined
    };

    expect(actions.addFactsError(error)).toEqual(expectedAction);
  });

  it('should create a POST loading action', () => {
    const loading = true;
    const expectedAction = {
      type: types.ADD_FACTS_LOADING,
      loading
    };

    expect(actions.addFactsLoading(loading)).toEqual(expectedAction);
  });

  it('should create a POST success action', () => {
    const data = {};
    const expectedAction = {
      type: types.ADD_FACTS_SUCCESS,
      data
    };

    expect(actions.addFactsSuccess(data)).toEqual(expectedAction);
  });
});
