import React from 'react';
import PropTypes from 'prop-types';
import JSONPretty from 'react-json-pretty';
import { ListView, Button, Icon, Checkbox } from 'patternfly-react';

class CredentialListItem extends React.Component {
  renderExpansionContents() {
    const { item } = this.props;

    return <JSONPretty json={item} />;
  }

  render() {
    const { item, onItemSelectChange } = this.props;

    let itemIcon;
    switch (item.cred_type) {
      case 'vcenter':
        itemIcon = <ListView.Icon type="pf" name="virtual-machine" />;
        break;
      case 'network':
        itemIcon = <ListView.Icon type="pf" name="network" />;
        break;
      case 'satellite':
        itemIcon = <ListView.Icon type="fa" name="space-shuttle" />;
        break;
      default:
        itemIcon = null;
    }

    let credentialType = 'Username & Password';
    if (item.auth_type === 'sshKey') {
      credentialType = 'SSH Key';
    } else if (item.auth_type === 'becomeUser') {
      credentialType = 'Become User';
    }

    return (
      <ListView.Item
        key={item.id}
        checkboxInput={
          <Checkbox
            checked={item.selected}
            bsClass=""
            onClick={e => onItemSelectChange(item)}
          />
        }
        actions={
          <span>
            <Button className="unavailable" bsStyle="link" key="editButton">
              <Icon type="pf" name="edit" />
            </Button>
            <Button className="unavailable" bsStyle="link" key="removeButton">
              <Icon type="pf" name="delete" />
            </Button>
          </span>
        }
        leftContent={itemIcon}
        heading={item.name}
        description={credentialType}
        additionalInfo={[
          <ListView.InfoItem
            key="userName"
            className="list-view-info-item-text-count"
          >
            {item.authType === 'becomeUser' ? item.become_user : item.username}
          </ListView.InfoItem>,
          <ListView.InfoItem
            key="becomeMethod"
            className="list-view-info-item-text-count"
          >
            {item.authType === 'becomeUser' ? item.become_method : ''}
          </ListView.InfoItem>
        ]}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
    );
  }
}

CredentialListItem.propTypes = {
  item: PropTypes.object,
  onItemSelectChange: PropTypes.func
};

export { CredentialListItem };
