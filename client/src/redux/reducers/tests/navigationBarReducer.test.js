import navigationBarReducer from '../navigationBarReducer';

describe('NavigationBarReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      collapsed: false
    };

    expect(navigationBarReducer(undefined, {})).toEqual(initialState);
  });
});
