import { sourcesTypes as types } from '../constants';
import * as actions from './sourcesActions';

describe('SourcesActions', function() {
  it('should create a GET error action', () => {
    const error = true;
    const expectedAction = {
      type: types.GET_SOURCES_ERROR,
      error,
      message: undefined
    };

    expect(actions.getSourcesError(error)).toEqual(expectedAction);
  });

  it('should create a GET loading action', () => {
    const loading = true;
    const expectedAction = {
      type: types.GET_SOURCES_LOADING,
      loading
    };

    expect(actions.getSourcesLoading(loading)).toEqual(expectedAction);
  });

  it('should create a GET success action', () => {
    const data = {};
    const expectedAction = {
      type: types.GET_SOURCES_SUCCESS,
      data
    };

    expect(actions.getSourcesSuccess(data)).toEqual(expectedAction);
  });
});
