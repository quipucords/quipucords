import reduxTypes, * as allReduxTypes from '..';

describe('ReduxTypes', () => {
  it('should have specific type properties', () => {
    expect(reduxTypes).toMatchSnapshot('specific types');

    expect(allReduxTypes).toMatchSnapshot('all redux types');
  });
});
