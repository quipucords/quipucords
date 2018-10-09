import React from 'react';
import configureMockStore from 'redux-mock-store';
import { shallow } from 'enzyme';
import CreateCredentialDialog from '../createCredentialDialog';

describe('CreateCredentialDialog Component', () => {
  const generateEmptyStore = () => configureMockStore()({ credentials: {}, viewOptions: {} });

  it('should shallow render a basic component', () => {
    const store = generateEmptyStore();
    const props = { show: true };
    const wrapper = shallow(<CreateCredentialDialog {...props} />, { context: { store } });

    expect(wrapper.dive()).toMatchSnapshot();
  });
});
