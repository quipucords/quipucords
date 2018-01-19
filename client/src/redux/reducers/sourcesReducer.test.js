import { sourcesTypes as types } from '../constants';
import sourcesReducer from './sourcesReducer';

describe('SourcesReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      error: false,
      errorMessage: '',
      loading: true,
      data: []
    };

    expect(sourcesReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_SOURCES_ERROR', () => {
    const dispatched = {
      type: types.GET_SOURCES_ERROR,
      error: true,
      message: 'error message'
    };

    expect(sourcesReducer(undefined, dispatched).error).toEqual(
      dispatched.error
    );
    expect(sourcesReducer(undefined, dispatched).errorMessage).toEqual(
      dispatched.message
    );
  });

  it('should handle GET_SOURCES_LOADING', () => {
    const dispatched = {
      type: types.GET_SOURCES_LOADING,
      loading: false
    };

    expect(sourcesReducer(undefined, dispatched).loading).toEqual(
      dispatched.loading
    );
  });

  it('should handle GET_SOURCES_SUCCESS', () => {
    const dispatched = {
      type: types.GET_SOURCES_SUCCESS,
      data: ['test']
    };

    expect(sourcesReducer(undefined, dispatched).data).toEqual(dispatched.data);
  });
});
