import React from 'react';
import PropTypes from 'prop-types';
import { ListView, Button, Icon, Checkbox } from 'patternfly-react';

class CredentialListItem extends React.Component {
  render() {
    const { item, onItemSelectChange, onEdit, onDelete } = this.props;

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

    let credentialType;
    switch (item.auth_type) {
      case 'sshKey':
        credentialType = 'SSH Key';
        break;
      case 'becomeUser':
        credentialType = 'Become User';
        break;
      default:
        credentialType = 'Username & Password';
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
            <Button
              onClick={() => {
                onEdit(item);
              }}
              bsStyle="link"
              key="editButton"
            >
              <Icon type="pf" name="edit" />
            </Button>
            <Button
              onClick={() => {
                onDelete(item);
              }}
              bsStyle="link"
              key="removeButton"
            >
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
      />
    );
  }
}

CredentialListItem.propTypes = {
  item: PropTypes.object,
  onItemSelectChange: PropTypes.func,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func
};

export { CredentialListItem };
