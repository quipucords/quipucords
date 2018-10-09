import React from 'react';
import { mount } from 'enzyme';
import CredentialsEmptyState from '../credentialsEmptyState';

describe('CredentialsEmptyState Component', () => {
  it('should render a basic component', () => {
    const props = {};

    const component = mount(<CredentialsEmptyState {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});
