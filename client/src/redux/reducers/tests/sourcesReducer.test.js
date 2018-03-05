import { sourcesTypes } from '../../constants/index';
import sourcesReducer from '../sourcesReducer';

const initialState = {
  persist: {
    selectedSources: []
  },

  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sources: []
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sourceId: '',
    delete: false
  }
};

describe('SourcesReducer', function() {
  it('should return the initial state', () => {
    expect(sourcesReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle SELECT_SOURCE and DESELECT_SOURCE', () => {
    let dispatched = {
      type: sourcesTypes.SELECT_SOURCE,
      source: { name: 'selected', id: 1 }
    };

    let resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.persist.selectedSources).toHaveLength(1);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.update).toEqual(initialState.update);

    dispatched.type = sourcesTypes.DESELECT_SOURCE;
    resultState = sourcesReducer(resultState, dispatched);

    expect(resultState.persist.selectedSources).toHaveLength(0);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle DELETE_SOURCE_REJECTED', () => {
    let dispatched = {
      type: sourcesTypes.DELETE_SOURCE_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'DELETE ERROR'
          }
        }
      }
    };

    let resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.update.error).toBeTruthy();
    expect(resultState.update.errorMessage).toEqual('DELETE ERROR');
    expect(resultState.update.delete).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
  });

  it('should handle GET_SOURCES_REJECTED', () => {
    let dispatched = {
      type: sourcesTypes.GET_SOURCES_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET ERROR'
          }
        }
      }
    };

    let resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.view.error).toBeTruthy();
    expect(resultState.view.errorMessage).toEqual('GET ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle GET_SOURCES_PENDING', () => {
    let dispatched = {
      type: sourcesTypes.GET_SOURCES_PENDING
    };

    let resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.view.pending).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.update).toEqual(initialState.update);
  });

  it('should handle GET_SOURCES_FULFILLED', () => {
    let dispatched = {
      type: sourcesTypes.GET_SOURCES_FULFILLED,
      payload: {
        data: {
          results: [
            {
              name: '1',
              id: 1
            },
            {
              name: '2',
              id: 2
            },
            {
              name: '3',
              id: 3
            },
            {
              name: '4',
              id: 4
            }
          ]
        }
      }
    };

    let resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.view.fulfilled).toBeTruthy();
    expect(resultState.view.sources).toHaveLength(4);

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.update).toEqual(initialState.update);
  });

  it('should maintain selections on new data', () => {
    let dispatched = {
      type: sourcesTypes.GET_SOURCES_FULFILLED,
      error: true,
      payload: {
        data: {
          results: [
            {
              name: '1',
              id: 1
            },
            {
              name: '2',
              id: 2
            },
            {
              name: '3',
              id: 3
            },
            {
              name: '4',
              id: 4
            }
          ]
        }
      }
    };

    let resultState = sourcesReducer(undefined, dispatched);

    expect(resultState.view.fulfilled).toBeTruthy();
    expect(resultState.view.sources).toHaveLength(4);

    dispatched = {
      type: sourcesTypes.SELECT_SOURCE,
      source: { name: '1', id: 1 }
    };

    resultState = sourcesReducer(resultState, dispatched);

    expect(resultState.persist.selectedSources).toHaveLength(1);

    dispatched = {
      type: sourcesTypes.SELECT_SOURCE,
      source: { name: '2', id: 2 }
    };

    resultState = sourcesReducer(resultState, dispatched);

    expect(resultState.persist.selectedSources).toHaveLength(2);

    dispatched = {
      type: sourcesTypes.GET_SOURCES_FULFILLED,
      error: true,
      payload: {
        data: {
          results: [
            {
              name: '1',
              id: 1
            },
            {
              name: '5',
              id: 5
            },
            {
              name: '6',
              id: 6
            },
            {
              name: '7',
              id: 7
            }
          ]
        }
      }
    };

    resultState = sourcesReducer(resultState, dispatched);
    expect(resultState.persist.selectedSources).toHaveLength(2);
  });
});
