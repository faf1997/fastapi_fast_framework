import pytest

def test_admin_bootstrap(env_test):
    User = env_test['res.users']
    admin = User.search([('id', '=', 1)])
    assert admin, "Admin user should exist"
    assert len(admin) == 1
    assert len(admin) == 1
    admin_rec = admin
    assert admin_rec.login == 'admin'
    assert admin_rec.name == 'Administrator'

def test_partner_crud(env_test):
    Partner = env_test['res.partner']
    
    # Create
    p = Partner.create({'name': 'Test Partner', 'email': 'test@example.com'})
    assert p.ids
    assert p.name == 'Test Partner'
    
    # Read
    data = p.read(['name', 'email'])
    assert data[0]['name'] == 'Test Partner'
    
    # Write
    p.write({'email': 'new@example.com'})
    assert p.read(['email'])[0]['email'] == 'new@example.com'
    
    # Search
    search_res = Partner.search([('name', '=', 'Test Partner')])
    assert p.ids[0] in search_res.ids
    
    # Unlink
    p.unlink()
    search_res = Partner.search([('name', '=', 'Test Partner')])
    assert not search_res.ids

def test_access_rights(env_test):
    # Create a non-admin user
    User = env_test['res.users']
    Partner = env_test['res.partner']
    
    # 1. Create a user
    user = User.create({'name': 'Demo User', 'login': 'demo', 'password': 'demo'})
    
    # 2. Switch environment to this user
    env_demo = env_test.__class__(env_test.cr, user.ids[0], {})
    PartnerDemo = env_demo['res.partner']
    
    # 3. Try to read partners -> Should fail (no access rights defined)
    with pytest.raises(Exception) as excinfo:
        PartnerDemo.search([])
    assert "Access Denied" in str(excinfo.value)
    
    # 4. Grant Read Access
    Access = env_test['ir.model.access']
    Access.create({
        'name': 'Partner Read',
        'model_id': 'res.partner',
        'user_id': user.ids[0],
        'perm_read': True,
        'perm_write': False,
        'perm_create': False,
        'perm_unlink': False
    })
    
    # 5. Try to read again -> Should succeed
    res = PartnerDemo.search([])
    assert isinstance(res.ids, list)
    
    # 6. Try to create -> Should fail
    with pytest.raises(Exception) as excinfo:
        PartnerDemo.create({'name': 'Hacker'})
    assert "Access Denied" in str(excinfo.value)

